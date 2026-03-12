"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api, streamChat } from "@/lib/api";

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

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const prescriptionId = searchParams.get("prescriptionId");
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "안녕하세요! AI 복약 상담 챗봇입니다. 복약과 관련하여 궁금하신 점을 물어보세요." },
  ]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<number | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 피드백 모달 상태
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackStep, setFeedbackStep] = useState<"rating" | "reason">("rating");
  const [selectedReason, setSelectedReason] = useState<string | null>(null);
  const [reasonText, setReasonText] = useState("");
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);

  const initThread = () => {
    setInitError(null);
    api
      .createThread(prescriptionId ? Number(prescriptionId) : undefined)
      .then((res) => {
        if (res.success && res.data) {
          setThreadId((res.data as { id: number }).id);
        } else {
          setInitError(res.error || "채팅을 시작할 수 없습니다. 로그인 상태를 확인해주세요.");
        }
      })
      .catch(() => {
        setInitError("서버에 연결할 수 없습니다.");
      });
  };

  useEffect(() => {
    initThread();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || !threadId || isStreaming) return;

    setInput("");
    setShowQuickActions(false);
    setIsStreaming(true);

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "", status: "streaming" }]);

    await streamChat(
      threadId,
      text,
      (chunk) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = { ...last, content: last.content + chunk };
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
        {/* Header */}
        <div className="bg-white rounded-t-lg border p-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">AI</div>
          <div className="flex-1">
            <h1 className="font-bold">AI 복약 상담 챗봇</h1>
            <p className="text-xs text-green-500">온라인</p>
          </div>
          <Link
            href="/chat/history"
            className="text-sm text-blue-600 hover:underline"
          >
            대화 기록
          </Link>
          <button
            onClick={handleEndClick}
            disabled={isStreaming || !threadId}
            className="text-sm border border-red-300 text-red-600 px-3 py-1 rounded-lg hover:bg-red-50 disabled:opacity-50"
          >
            상담 종료
          </button>
        </div>

        {/* Init Error */}
        {initError && (
          <div className="bg-red-50 border-x border-red-200 p-4 text-center">
            <p className="text-red-600 text-sm mb-2">{initError}</p>
            <button
              onClick={initThread}
              className="text-sm text-blue-600 hover:underline"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Messages */}
        <div className="bg-white border-x p-4 min-h-[400px] max-h-[500px] overflow-y-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[70%] rounded-lg p-3 whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-blue-600 text-white text-sm"
                  : msg.status === "failed"
                    ? "bg-red-100 text-red-800 text-base"
                    : "bg-gray-100 text-gray-800 text-base"
              }`}>
                {msg.content || (msg.status === "streaming" ? (
                  <span className="inline-flex gap-1 py-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </span>
                ) : "")}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick actions */}
        {showQuickActions && (
          <div className="bg-white border-x px-4 pb-2">
            <p className="text-xs text-gray-400 mb-2">자주 묻는 질문</p>
            <div className="grid grid-cols-2 gap-2">
              {quickActions.map((q) => (
                <button key={q} onClick={() => sendMessage(q)} className="text-sm border rounded-lg px-3 py-3 text-left hover:bg-gray-50">
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="bg-white rounded-b-lg border p-4">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.nativeEvent.isComposing && sendMessage(input)}
              placeholder="메시지를 입력하세요..."
              className="flex-1 border rounded-lg px-4 py-3 text-base"
              disabled={isStreaming}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={isStreaming}
              className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              전송
            </button>
          </div>
          <p className="text-xs text-gray-400 text-center mt-2">{DISCLAIMER}</p>
        </div>

        {/* Info box */}
        <div className="bg-blue-50 rounded-lg p-4 mt-4 text-sm">
          <p className="font-bold mb-1">AI 챗봇 사용 안내</p>
          <ul className="list-disc list-inside text-gray-600 space-y-1">
            <li>복약 방법, 시간, 주의사항 등에 대해 질문할 수 있습니다.</li>
            <li>약물 상호작용이나 부작용에 대해 문의할 수 있습니다.</li>
            <li>긴급한 상황이나 심각한 증상은 즉시 의료기관에 연락하세요.</li>
          </ul>
        </div>
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            {feedbackStep === "rating" ? (
              <>
                <h2 className="text-lg font-bold text-center mb-2">상담이 도움이 되셨나요?</h2>
                <p className="text-sm text-gray-500 text-center mb-6">
                  피드백을 남겨주시면 서비스 개선에 큰 도움이 됩니다.
                </p>
                <div className="flex justify-center gap-6 mb-6">
                  <button
                    onClick={handlePositiveFeedback}
                    disabled={feedbackSubmitting}
                    className="flex flex-col items-center gap-2 px-6 py-4 border rounded-lg hover:bg-blue-50 disabled:opacity-50"
                  >
                    <span className="text-3xl">👍</span>
                    <span className="text-sm font-medium">도움이 됐어요</span>
                  </button>
                  <button
                    onClick={handleNegativeFeedback}
                    disabled={feedbackSubmitting}
                    className="flex flex-col items-center gap-2 px-6 py-4 border rounded-lg hover:bg-red-50 disabled:opacity-50"
                  >
                    <span className="text-3xl">👎</span>
                    <span className="text-sm font-medium">아쉬웠어요</span>
                  </button>
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={handleSkipFeedback}
                    disabled={feedbackSubmitting}
                    className="w-full text-sm text-gray-400 hover:text-gray-600 disabled:opacity-50"
                  >
                    피드백 없이 종료
                  </button>
                  <button
                    onClick={() => { setShowFeedbackModal(false); setFeedbackSubmitting(false); }}
                    disabled={feedbackSubmitting}
                    className="w-full text-sm text-blue-500 hover:text-blue-700 disabled:opacity-50"
                  >
                    취소
                  </button>
                </div>
              </>
            ) : (
              <>
                <h2 className="text-lg font-bold mb-2">어떤 점이 아쉬우셨나요?</h2>
                <p className="text-sm text-gray-500 mb-4">사유를 선택해주세요.</p>
                <div className="space-y-2 mb-4">
                  {negativeReasons.map((r) => (
                    <button
                      key={r.value}
                      onClick={() => setSelectedReason(r.value)}
                      className={`w-full text-left text-sm px-4 py-3 border rounded-lg ${
                        selectedReason === r.value
                          ? "border-blue-500 bg-blue-50 text-blue-700"
                          : "hover:bg-gray-50"
                      }`}
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
                    className="w-full border rounded-lg px-3 py-2 text-sm mb-4 resize-none"
                    rows={3}
                  />
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => setFeedbackStep("rating")}
                    disabled={feedbackSubmitting}
                    className="flex-1 border py-2 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
                  >
                    뒤로
                  </button>
                  <button
                    onClick={handleSubmitNegativeFeedback}
                    disabled={!selectedReason || feedbackSubmitting}
                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
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
