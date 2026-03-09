"use client";

import { useEffect, useRef, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { api, streamChat } from "@/lib/api";

const DISCLAIMER = "AI가 제공하는 정보는 참고용입니다. 정확한 진단과 처방은 의료 전문가와 상담하세요.";

const quickActions = [
  "약을 식전에 먹어야 하나요?",
  "부작용이 나타나면 어떻게 하나요?",
  "다른 약과 함께 먹어도 되나요?",
  "약을 깜빡하고 안 먹었어요",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  status?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "안녕하세요! AI 복약 상담 챗봇입니다. 복약과 관련하여 궁금하신 점을 물어보세요." },
  ]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<number | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.createThread().then((res) => {
      if (res.success && res.data) {
        setThreadId((res.data as { id: number }).id);
      }
    });
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
        </div>

        {/* Messages */}
        <div className="bg-white border-x p-4 min-h-[400px] max-h-[500px] overflow-y-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[70%] rounded-lg p-3 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : msg.status === "failed"
                    ? "bg-red-100 text-red-800"
                    : "bg-gray-100 text-gray-800"
              }`}>
                {msg.content || (msg.status === "streaming" ? "..." : "")}
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
                <button key={q} onClick={() => sendMessage(q)} className="text-sm border rounded-lg px-3 py-2 text-left hover:bg-gray-50">
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
              className="flex-1 border rounded-lg px-4 py-2"
              disabled={isStreaming}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={isStreaming}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
    </AppLayout>
  );
}
