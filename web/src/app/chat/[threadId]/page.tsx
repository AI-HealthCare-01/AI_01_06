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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMessages(threadId)
      .then((res) => {
        if (res.success && res.data) {
          setMessages(res.data as MessageItem[]);
        } else {
          setError(res.error || "대화 내용을 불러오지 못했습니다.");
        }
      })
      .catch(() => {
        setError("서버 연결에 실패했습니다.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [threadId]);

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <Link
            href="/chat/history"
            className="text-sm text-blue-600 hover:underline"
          >
            &lt; 대화 기록으로
          </Link>
        </div>

        <div className="bg-white rounded-t-lg border p-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
            AI
          </div>
          <div className="flex-1">
            <h1 className="font-bold">대화 상세</h1>
            <p className="text-xs text-gray-400">읽기 전용</p>
          </div>
        </div>

        {/* Messages */}
        <div className="bg-white border-x border-b rounded-b-lg p-4 min-h-[400px] max-h-[600px] overflow-y-auto space-y-4">
          {loading ? (
            <p className="text-gray-500 text-center py-8">로딩 중...</p>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center text-red-600">
              {error}
            </div>
          ) : messages.length === 0 ? (
            <p className="text-gray-400 text-center py-8">
              대화 내용이 없습니다.
            </p>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[70%] rounded-lg p-3 text-sm whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : msg.status === "failed"
                        ? "bg-red-100 text-red-800"
                        : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {msg.content}
                  <p
                    className={`text-xs mt-1 ${
                      msg.role === "user" ? "text-blue-200" : "text-gray-400"
                    }`}
                  >
                    {msg.created_at.slice(11, 16)}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 rounded-lg p-4 mt-4 text-sm text-center text-gray-500">
          이 대화는 종료되었습니다.{" "}
          <Link href="/chat" className="text-blue-600 hover:underline">
            새 상담 시작하기
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}
