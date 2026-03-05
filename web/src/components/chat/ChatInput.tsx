'use client';

import { useState } from 'react';

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('');

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  };

  return (
    <div className="flex items-end gap-3 bg-white border-t-2 border-gray-200 px-4 py-4">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
        placeholder="궁금한 점을 입력하세요..."
        rows={2}
        disabled={disabled}
        className="flex-1 border-2 border-gray-300 rounded-xl px-4 py-3 text-lg resize-none focus:outline-none focus:border-blue-400 disabled:bg-gray-50"
      />
      <button
        onClick={handleSend}
        disabled={!text.trim() || disabled}
        className="w-14 h-14 rounded-xl text-white text-2xl flex items-center justify-center disabled:opacity-40 shrink-0"
        style={{ backgroundColor: '#4a90e2' }}
        aria-label="전송"
      >
        ↑
      </button>
    </div>
  );
}
