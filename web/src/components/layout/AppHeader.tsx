'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function AppHeader() {
  const [large, setLarge] = useState(false);

  const toggleFontSize = () => {
    document.body.classList.toggle('large-text');
    setLarge((prev) => !prev);
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-screen-xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link
          href="/"
          className="text-2xl font-extrabold tracking-tight"
          style={{ color: '#4a90e2' }}
        >
          &amp; 설리반
        </Link>
        <nav className="flex items-center gap-3">
          <button
            onClick={toggleFontSize}
            className="text-sm text-gray-500 border border-gray-300 rounded-lg px-3 py-1.5 hover:bg-gray-50"
            aria-label="글씨 크기 조절"
            aria-pressed={large}
          >
            가 / 가
          </button>
          <Link
            href="/login"
            className="text-lg font-semibold text-gray-700 border border-gray-300 rounded-xl px-5 py-2 hover:bg-gray-50"
          >
            로그인
          </Link>
          <Link
            href="/signup"
            className="text-lg font-semibold text-white rounded-xl px-5 py-2 hover:opacity-90"
            style={{ backgroundColor: '#4a90e2' }}
          >
            회원가입
          </Link>
        </nav>
      </div>
    </header>
  );
}
