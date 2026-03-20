"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api, streamChat } from "@/lib/api";
import { usePatient } from "@/lib/patient-context";

const DISCLAIMER = "AI가 제공하는 정보는 참고용입니다. 정확한 진단과 처방은 의료 전문가와 상담하세요.";

const quickActions = [
  "약을 식전에 먹어야 하나요?",
  "부작용이 나타나면 어떻게 하나요?",
  "다른 약과 함께 먹어도 되나요?",
  "약을 깜빡하고 안 먹었어요",
];

const negativeReasons = [
  { value: "inaccurate", label: "정보가 정확하지 않았어요" },
  { value: "unhelpful", label: "도움이 되지 않았어요" },
  { value: "hard_to_understand", label: "이해하기 어려웠어요" },
  { value: "other", label: "기타" },
];

interface Message {
  role: "user" | "assistant";
  content: string;
  status?: string;
}

function ChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const prescriptionId = searchParams.get("prescriptionId");
  const resumeThreadId = searchParams.get("threadId");
  const { activePatient, isProxyMode } = usePatient();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "안녕하세요. 복약 상담을 도와드리는 설리반입니다. 약을 드시면서 궁금한 점이 있으시면 편하게 말씀해 주세요." },
  ]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<number | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [quickActionsOpen, setQuickActionsOpen] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 피드백 모달 상태
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackStep, setFeedbackStep] = useState<"rating" | "reason">("rating");
  const [selectedReason, setSelectedReason] = useState<string | null>(null);
  const [reasonText, setReasonText] = useState("");
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);

  const initThread = async () => {
    setInitError(null);
    try {
      if (resumeThreadId) {
        // 기존 스레드 이어가기
        const threadRes = await api.getThread(Number(resumeThreadId));
        if (!threadRes.success || !threadRes.data) {
          setInitError(threadRes.error || "대화를 불러올 수 없습니다.");
          return;
        }
        const thread = threadRes.data as { id: number; status: string };

        // ended/auto_closed → reactivate
        if (thread.status === "ended" || thread.status === "auto_closed") {
          const reactRes = await api.reactivateThread(thread.id);
          if (!reactRes.success) {
            setInitError(reactRes.error || "대화를 재개할 수 없습니다.");
            return;
          }
        }

        // 기존 메시지 로드
        const msgRes = await api.getMessages(Number(resumeThreadId));
        if (msgRes.success && msgRes.data) {
          const loaded = (msgRes.data as Array<{ role: "user" | "assistant"; content: string; status?: string }>);
          if (loaded.length > 0) {
            setMessages(loaded.map((m) => ({ role: m.role, content: m.content, status: m.status })));
            setQuickActionsOpen(false);
          }
        }
        setThreadId(Number(resumeThreadId));
      }
      // 새 채팅: thread는 첫 메시지 전송 시 생성 (lazy creation)
    } catch {
      setInitError("서버에 연결할 수 없습니다.");
    }
  };

  useEffect(() => {
    initThread();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    // Lazy thread creation: 첫 메시지 시점에 thread 생성
    let currentThreadId = threadId;
    if (!currentThreadId) {
      try {
        const res = await api.createThread(prescriptionId ? Number(prescriptionId) : undefined);
        if (!res.success || !res.data) {
          setInitError(res.error || "채팅을 시작할 수 없습니다. 로그인 상태를 확인해주세요.");
          return;
        }
        currentThreadId = (res.data as { id: number }).id;
        setThreadId(currentThreadId);
      } catch {
        setInitError("서버에 연결할 수 없습니다.");
        return;
      }
    }

    setInput("");
    setQuickActionsOpen(false);
    setIsStreaming(true);

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "", status: "streaming" }]);

    await streamChat(
      currentThreadId,
      text,
      (content) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = { ...last, content };
          }
          return updated;
        });
      },
      () => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = { ...last, status: "completed" };
          }
          return updated;
        });
        setIsStreaming(false);
      },
      (errorMsg) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = {
              ...last,
              content: errorMsg || "오류가 발생했습니다.",
              status: "failed",
            };
          }
          return updated;
        });
        setIsStreaming(false);
      },
    );
  };

  const endThreadAndRedirect = async () => {
    if (threadId) {
      await api.endThread(threadId);
    }
    router.push("/chat/history");
  };

  const handleEndClick = () => {
    if (!threadId || isStreaming) return;
    setShowFeedbackModal(true);
    setFeedbackStep("rating");
    setSelectedReason(null);
    setReasonText("");
  };

  const handlePositiveFeedback = async () => {
    if (!threadId) return;
    setFeedbackSubmitting(true);
    await api.sendFeedback({ thread_id: threadId, feedback_type: "session_positive" });
    await endThreadAndRedirect();
  };

  const handleNegativeFeedback = () => {
    setFeedbackStep("reason");
  };

  const handleSubmitNegativeFeedback = async () => {
    if (!threadId || !selectedReason) return;
    setFeedbackSubmitting(true);
    await api.sendFeedback({
      thread_id: threadId,
      feedback_type: "session_negative",
      reason: selectedReason,
      reason_text: reasonText || undefined,
    });
    await endThreadAndRedirect();
  };

  const handleSkipFeedback = async () => {
    setFeedbackSubmitting(true);
    await endThreadAndRedirect();
  };

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        {/* ── Single unified card ── */}
        <div className="app-card overflow-hidden flex flex-col" style={{ maxHeight: 'calc(100dvh - 8rem)' }}>

          {/* Header — 모바일 2줄 / 웹 1줄 */}
          <div className="px-5 py-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
            <div className="flex items-center gap-3 md:gap-4">
              <div className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0" style={{ background: 'var(--color-primary-soft)' }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="var(--color-primary)"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-base font-bold leading-snug">AI 복약 상담</h1>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: 'var(--color-success)' }} />
                  <p className="text-sm" style={{ color: 'var(--color-success)' }}>온라인</p>
                </div>
              </div>
              {/* 웹: 1줄에 액션 버튼 표시 */}
              <div className="hidden md:flex items-center gap-3">
                <Link
                  href="/chat/history"
                  className="text-sm px-4 py-2.5 rounded-xl hover:underline"
                  style={{ color: 'var(--color-primary)' }}
                >
                  대화 기록
                </Link>
                <button
                  onClick={handleEndClick}
                  disabled={isStreaming || !threadId}
                  className="text-sm px-4 py-2.5 min-h-[44px] rounded-xl disabled:opacity-50 transition-colors btn-danger-outline"
                >
                  상담 종료
                </button>
              </div>
            </div>
            {/* 모바일: 2행에 액션 버튼 표시 */}
            <div className="flex md:hidden items-center justify-end gap-3 mt-3">
              <Link
                href="/chat/history"
                className="text-sm px-4 py-2.5 min-h-[44px] flex items-center rounded-xl btn-outline"
              >
                대화 기록
              </Link>
              <button
                onClick={handleEndClick}
                disabled={isStreaming || !threadId}
                className="text-sm px-4 py-2.5 min-h-[44px] rounded-xl disabled:opacity-50 transition-colors btn-danger-outline"
              >
                상담 종료
              </button>
            </div>
          </div>

          {/* Proxy mode banner */}
          {isProxyMode && activePatient && (
            <div
              className="px-5 py-2.5 text-sm"
              style={{
                backgroundColor: "var(--color-primary-soft)",
                color: "var(--color-primary)",
                borderBottom: "1px solid var(--color-border)",
              }}
            >
              이 상담은 <strong>{activePatient.name}</strong>님에 대한 상담입니다.
              {activePatient.name}님의 건강 정보를 바탕으로 답변합니다.
            </div>
          )}

          {/* Init Error */}
          {initError && (
            <div className="px-5 py-4 text-center" style={{ background: 'var(--color-danger-soft)', borderBottom: '1px solid var(--color-border)' }}>
              <p className="text-sm mb-2" style={{ color: 'var(--color-danger)' }}>{initError}</p>
              <button
                onClick={initThread}
                className="text-sm hover:underline"
                style={{ color: 'var(--color-primary)' }}
              >
                다시 시도
              </button>
            </div>
          )}

          {/* Messages — scrollable area */}
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4" style={{ minHeight: '240px' }}>
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] md:max-w-[75%] rounded-2xl px-4 py-3 whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "text-white text-sm"
                    : "text-base"
                }`} style={
                  msg.role === "user"
                    ? { background: 'var(--color-primary)' }
                    : msg.status === "failed"
                      ? { background: 'var(--color-danger-soft)', color: 'var(--color-danger-text)' }
                      : { background: 'var(--color-surface)', color: 'var(--color-text)' }
                }>
                  {msg.content || (msg.status === "streaming" ? (
                    <span className="inline-flex gap-1 py-1">
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-muted)', animationDelay: "0ms" }} />
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-muted)', animationDelay: "150ms" }} />
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-muted)', animationDelay: "300ms" }} />
                    </span>
                  ) : "")}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick actions — toggle persists after chat starts */}
          <div className="shrink-0 px-5 py-3" style={{ borderTop: '1px solid var(--color-border)' }}>
            <button
              type="button"
              onClick={() => setQuickActionsOpen((v) => !v)}
              className="flex items-center gap-1.5 text-sm cursor-pointer"
              style={{ color: 'var(--color-text-muted)' }}
              aria-expanded={quickActionsOpen}
            >
              <svg
                width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"
                className="transition-transform duration-200"
                style={{ transform: quickActionsOpen ? 'rotate(90deg)' : 'rotate(0deg)' }}
              >
                <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z" />
              </svg>
              자주 묻는 질문
            </button>
            {quickActionsOpen && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                {quickActions.map((q) => (
                  <button key={q} onClick={() => sendMessage(q)} className="text-sm rounded-xl px-4 py-3.5 text-left btn-outline">
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Input — inside card, sticky within the flex column */}
          <div className="shrink-0 px-5 py-4" style={{ borderTop: '1px solid var(--color-border)' }}>
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.nativeEvent.isComposing && sendMessage(input)}
                onFocus={(e) => { setTimeout(() => e.target.scrollIntoView({ block: "center", behavior: "smooth" }), 300); }}
                placeholder="메시지를 입력하세요..."
                className="flex-1 px-4 py-3 text-base input-field"
                disabled={isStreaming}
              />
              <button
                onClick={() => sendMessage(input)}
                disabled={isStreaming}
                className="px-5 py-3 min-h-[44px] rounded-xl btn-primary"
              >
                전송
              </button>
            </div>
            <p className="text-sm text-center mt-2" style={{ color: 'var(--color-text-muted)' }}>{DISCLAIMER}</p>
          </div>

        </div>{/* end single unified card */}

        {/* Info box */}
        <div className="rounded-2xl p-5 mt-4 text-sm" style={{ background: 'var(--color-primary-soft)' }}>
          <p className="font-bold mb-1">AI 챗봇 사용 안내</p>
          <ul className="list-disc list-inside space-y-1" style={{ color: 'var(--color-text-muted)' }}>
            <li>복약 방법, 시간, 주의사항 등에 대해 질문할 수 있습니다.</li>
            <li>약물 상호작용이나 부작용에 대해 문의할 수 있습니다.</li>
            <li>긴급한 상황이나 심각한 증상은 즉시 의료기관에 연락하세요.</li>
          </ul>
        </div>
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="rounded-2xl p-6 w-full max-w-md mx-4" style={{ background: 'var(--color-card-bg)', boxShadow: 'var(--shadow-lg)' }}>
            {feedbackStep === "rating" ? (
              <>
                <h2 className="text-lg font-bold text-center mb-2">상담이 도움이 되셨나요?</h2>
                <p className="text-sm text-center mb-6" style={{ color: 'var(--color-text-muted)' }}>
                  피드백을 남겨주시면 서비스 개선에 큰 도움이 됩니다.
                </p>
                <div className="flex justify-center gap-6 mb-6">
                  <button
                    onClick={handlePositiveFeedback}
                    disabled={feedbackSubmitting}
                    className="flex flex-col items-center gap-3 px-8 py-5 rounded-2xl disabled:opacity-50 btn-outline"
                  >
                    <span className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-primary-soft)' }}>
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="var(--color-primary)"><path d="M2 20h2V8H2v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L15.17 1 7.59 8.59C7.22 8.95 7 9.45 7 10v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>
                    </span>
                    <span className="text-sm font-semibold">도움이 됐어요</span>
                  </button>
                  <button
                    onClick={handleNegativeFeedback}
                    disabled={feedbackSubmitting}
                    className="flex flex-col items-center gap-3 px-8 py-5 rounded-2xl disabled:opacity-50 btn-outline"
                  >
                    <span className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-danger-soft)' }}>
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="var(--color-danger)"><path d="M22 4h-2v12h2V4zm-4 12V6c0-1.1-.9-2-2-2H7c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L8.83 23l7.58-7.59c.37-.36.59-.86.59-1.41z"/></svg>
                    </span>
                    <span className="text-sm font-semibold">아쉬웠어요</span>
                  </button>
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={handleSkipFeedback}
                    disabled={feedbackSubmitting}
                    className="w-full text-sm disabled:opacity-50"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    피드백 없이 종료
                  </button>
                  <button
                    onClick={() => { setShowFeedbackModal(false); setFeedbackSubmitting(false); }}
                    disabled={feedbackSubmitting}
                    className="w-full text-sm disabled:opacity-50"
                    style={{ color: 'var(--color-primary)' }}
                  >
                    취소
                  </button>
                </div>
              </>
            ) : (
              <>
                <h2 className="text-lg font-bold mb-2">어떤 점이 아쉬우셨나요?</h2>
                <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>사유를 선택해주세요.</p>
                <div className="space-y-2 mb-4">
                  {negativeReasons.map((r) => (
                    <button
                      key={r.value}
                      onClick={() => setSelectedReason(r.value)}
                      className="w-full text-left text-sm px-4 py-3.5 rounded-xl transition-colors"
                      style={
                        selectedReason === r.value
                          ? { border: '1px solid var(--color-primary)', background: 'var(--color-primary-soft)', color: 'var(--color-primary)' }
                          : { border: '1px solid var(--color-border)' }
                      }
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
                {selectedReason === "other" && (
                  <textarea
                    value={reasonText}
                    onChange={(e) => setReasonText(e.target.value)}
                    placeholder="자세한 내용을 입력해주세요 (선택)"
                    className="w-full px-3 py-2 text-sm mb-4 resize-none input-field"
                    rows={3}
                  />
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => setFeedbackStep("rating")}
                    disabled={feedbackSubmitting}
                    className="flex-1 py-2 rounded-lg text-sm disabled:opacity-50 btn-outline"
                  >
                    뒤로
                  </button>
                  <button
                    onClick={handleSubmitNegativeFeedback}
                    disabled={!selectedReason || feedbackSubmitting}
                    className="flex-1 py-2 rounded-lg text-sm btn-primary"
                  >
                    제출
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <AppLayout>
        <div className="max-w-3xl mx-auto p-4 text-center" style={{ color: "var(--color-text-muted)" }}>
          로딩 중...
        </div>
      </AppLayout>
    }>
      <ChatContent />
    </Suspense>
  );
}
