import type { ChatMessage } from '@/lib/api/types';

interface Props {
  messages: ChatMessage[];
}

export default function MessageList({ messages }: Props) {
  return (
    <div className="flex flex-col gap-4 py-4">
      {messages.map((msg) => {
        const isUser = msg.sender_type === 'USER';
        return (
          <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            {!isUser && (
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-xl mr-2 shrink-0">
                🤖
              </div>
            )}
            <div className={`max-w-[80%] px-5 py-4 rounded-2xl text-lg leading-relaxed ${
              isUser
                ? 'text-white rounded-br-sm'
                : 'bg-white border-2 border-gray-200 text-gray-800 rounded-bl-sm'
            }`}
              style={isUser ? { backgroundColor: '#4a90e2' } : {}}>
              {msg.message_text}
            </div>
          </div>
        );
      })}
    </div>
  );
}
