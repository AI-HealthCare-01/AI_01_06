"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface MessageItem {
  id: number;
  role: "user" | "assistant";
  content: string;
  status: string;
  created_at: string;
}

export default function ChatDetailPage() {
  const params = useParams();
  const threadId = Number(params.threadId);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [threadStatus, setThreadStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getThread(threadId), api.getMessages(threadId)])
      .then(([threadRes, msgRes]) => {
        if (threadRes.success && threadRes.data) {
          setThreadStatus((threadRes.data as { status: string }).status);
        }
        if (msgRes.success && msgRes.data) {
          setMessages(msgRes.data as MessageItem[]);
        } else {
          setError(msgRes.error || "대화 내용을 불러오지 못했습니다.");
        }
      })
      .catch(() => {
        setError("서버 연결에 실패했습니다.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [threadId]);

  const isEnded = threadStatus === "ended" || threadStatus === "auto_closed";

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        {/* Header navigation */}
        <div className="flex items-center justify-between mb-4">
          <Link
            href="/chat/history"
            className="text-sm hover:underline"
            style={{ color: "var(--color-primary)" }}
          >
            &lt; 대화 기록으로
          </Link>
        </div>

        {/* ── Single unified card ── */}
        <div className="app-card overflow-hidden flex flex-col" style={{ maxHeight: 'calc(100dvh - 10rem)' }}>

          {/* Header — 모바일 2줄 / 웹 1줄 */}
          <div className="px-5 py-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
            <div className="flex items-center gap-3 md:gap-4">
              <div className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0" style={{ background: "var(--color-primary-soft)" }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="var(--color-primary)"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-base font-bold leading-snug">대화 상세</h1>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: threadStatus === "active" ? "var(--color-success)" : "var(--color-text-muted)" }} />
                  <p className="text-sm" style={{ color: threadStatus === "active" ? "var(--color-success)" : "var(--color-text-muted)" }}>
                    {threadStatus === "active" ? "진행 중" : "읽기 전용"}
                  </p>
                </div>
              </div>
              {/* 웹: 1줄에 버튼 표시 */}
              {isEnded && (
                <Link
                  href={`/chat?threadId=${threadId}`}
                  className="hidden md:flex px-4 py-2.5 min-h-[44px] items-center rounded-xl text-sm font-semibold text-white transition-colors btn-primary"
                >
                  대화 이어가기
                </Link>
              )}
            </div>
            {/* 모바일: 2행에 버튼 표시 */}
            {isEnded && (
              <div className="flex md:hidden justify-end mt-3">
                <Link
                  href={`/chat?threadId=${threadId}`}
                  className="px-4 py-2.5 min-h-[44px] flex items-center rounded-xl text-sm font-semibold text-white transition-colors btn-primary"
                >
                  대화 이어가기
                </Link>
              </div>
            )}
          </div>

          {/* Messages — scrollable */}
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4" style={{ minHeight: '240px' }}>
            {loading ? (
              <p className="text-center py-8" style={{ color: "var(--color-text-muted)" }}>로딩 중...</p>
            ) : error ? (
              <div className="alert-danger rounded-lg p-8 text-center">{error}</div>
            ) : messages.length === 0 ? (
              <p className="text-center py-8" style={{ color: "var(--color-text-muted)" }}>
                대화 내용이 없습니다.
              </p>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] md:max-w-[75%] rounded-2xl px-4 py-3 whitespace-pre-wrap ${
                      msg.role === "user" ? "text-white text-sm" : "text-base"
                    }`}
                    style={
                      msg.role === "user"
                        ? { background: "var(--color-primary)" }
                        : msg.status === "failed"
                          ? { background: "var(--color-danger-soft)", color: "var(--color-danger-text)" }
                          : { background: "var(--color-surface)", color: "var(--color-text)" }
                    }
                  >
                    {msg.content}
                    <p
                      className="text-xs mt-1"
                      style={{
                        color: msg.role === "user" ? "rgba(255,255,255,0.6)" : "var(--color-text-muted)",
                      }}
                    >
                      {msg.created_at.slice(11, 16)}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div
            className="px-5 py-4 text-sm text-center shrink-0"
            style={{
              background: "var(--color-surface)",
              borderTop: "1px solid var(--color-border)",
            }}
          >
            {threadStatus === "active" ? (
              <p style={{ color: "var(--color-text-muted)" }}>
                이 대화는 진행 중입니다.{" "}
                <Link
                  href={`/chat?threadId=${threadId}`}
                  className="hover:underline"
                  style={{ color: "var(--color-primary)" }}
                >
                  대화로 돌아가기
                </Link>
              </p>
            ) : (
              <p style={{ color: "var(--color-text-muted)" }}>이 대화는 종료되었습니다.</p>
            )}
          </div>

        </div>{/* end single unified card */}
      </div>
    </AppLayout>
  );
}
