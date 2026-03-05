'use client';

import { useState, useRef, useEffect } from 'react';
import MessageList from '@/components/chat/MessageList';
import ChatInput from '@/components/chat/ChatInput';
import QuickChips from '@/components/chat/QuickChips';
import Disclaimer from '@/components/common/Disclaimer';
import type { ChatMessage } from '@/lib/api/types';

// TODO: API 연동
const MOCK_SESSION_ID = 'mock-session-1';

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      session_id: MOCK_SESSION_ID,
      sender_type: 'AI',
      message_text: '안녕하세요! 복약에 관해 궁금한 점을 편하게 물어보세요. 😊',
      created_at: new Date().toISOString(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      session_id: MOCK_SESSION_ID,
      sender_type: 'USER',
      message_text: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      // TODO: API 연동 - 스트리밍 응답 처리
      await new Promise((r) => setTimeout(r, 1000));
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        session_id: MOCK_SESSION_ID,
        sender_type: 'AI',
        message_text: '죄송합니다, 현재 AI 서버와 연결 중입니다. 잠시 후 다시 시도해 주세요.\n\n⚠️ 이 답변은 의료 전문가의 진단을 대체하지 않습니다.',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* 헤더 */}
      <div className="bg-white border-b-2 border-gray-200 px-4 py-4">
        <h1 className="text-2xl font-extrabold text-gray-900">AI 복약 상담</h1>
        <p className="text-gray-500 text-base">복약에 관한 궁금한 점을 물어보세요</p>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto px-4">
        <MessageList messages={messages} />
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-xl mr-2">🤖</div>
            <div className="bg-white border-2 border-gray-200 rounded-2xl rounded-bl-sm px-5 py-4">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 면책 문구 */}
      <div className="px-4 py-2">
        <Disclaimer />
      </div>

      {/* 퀵 칩 */}
      <QuickChips onSelect={sendMessage} disabled={loading} />

      {/* 입력창 */}
      <ChatInput onSend={sendMessage} disabled={loading} />
    </div>
  );
}
