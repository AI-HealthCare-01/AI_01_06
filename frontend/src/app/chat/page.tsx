"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";

const DISCLAIMER = "AI가 제공하는 정보는 참고용입니다. 정확한 진단과 처방은 의료 전문가와 상담하세요.";

const quickActions = [
  "약을 식전에 먹어야 하나요?",
  "부작용이 나타나면 어떻게 하나요?",
  "다른 약과 함께 먹어도 되나요?",
  "약을 깜빡하고 안 먹었어요",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "안녕하세요! AI 복약 상담 챗봇입니다. 복약과 관련하여 궁금하신 점을 물어보세요." },
  ]);
  const [input, setInput] = useState("");

  const sendMessage = (text: string) => {
    if (!text.trim()) return;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "죄송합니다. 현재 AI 상담 기능은 준비 중입니다. 빠른 시일 내에 서비스를 제공하겠습니다.\n\n" + DISCLAIMER },
    ]);
    setInput("");
  };

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-t-lg border p-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">AI</div>
          <div>
            <h1 className="font-bold">AI 복약 상담 챗봇</h1>
            <p className="text-xs text-green-500">온라인</p>
          </div>
        </div>

        {/* Messages */}
        <div className="bg-white border-x p-4 min-h-[400px] space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[70%] rounded-lg p-3 text-sm ${
                msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-800"
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        {/* Quick actions */}
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

        {/* Input */}
        <div className="bg-white rounded-b-lg border p-4">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
              placeholder="메시지를 입력하세요..."
              className="flex-1 border rounded-lg px-4 py-2"
            />
            <button onClick={() => sendMessage(input)} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
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
