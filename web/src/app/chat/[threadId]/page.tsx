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

        <div
          className="rounded-t-lg p-4 flex items-center gap-3"
          style={{ background: "var(--color-card-bg)", border: "1px solid var(--color-border)" }}
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
            style={{ background: "var(--color-primary)" }}
          >
            AI
          </div>
          <div className="flex-1">
            <h1 className="font-bold">대화 상세</h1>
            <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
              {threadStatus === "active" ? "진행 중" : "읽기 전용"}
            </p>
          </div>
          {isEnded && (
            <Link
              href={`/chat?threadId=${threadId}`}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-white transition-colors"
              style={{ background: "var(--color-cta)" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "var(--color-cta-hover)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "var(--color-cta)")}
            >
              대화 이어가기
            </Link>
          )}
        </div>

        {/* Messages */}
        <div
          className="p-4 min-h-[400px] max-h-[600px] overflow-y-auto space-y-4"
          style={{
            background: "var(--color-card-bg)",
            borderLeft: "1px solid var(--color-border)",
            borderRight: "1px solid var(--color-border)",
          }}
        >
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
                  className={`max-w-[70%] rounded-lg p-3 text-sm whitespace-pre-wrap ${
                    msg.role === "user" ? "text-white" : ""
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
          className="rounded-b-lg p-4 text-sm text-center"
          style={{
            background: "var(--color-surface)",
            borderLeft: "1px solid var(--color-border)",
            borderRight: "1px solid var(--color-border)",
            borderBottom: "1px solid var(--color-border)",
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
      </div>
    </AppLayout>
  );
}
