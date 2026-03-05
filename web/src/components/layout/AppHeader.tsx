'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { isLoggedIn } from '@/lib/auth/token';
import { useRouter } from 'next/navigation';
import { removeToken } from '@/lib/auth/token';

const NAV_ITEMS = [
  { href: '/dashboard', label: '홈', emoji: '🏠' },
  { href: '/prescriptions/list', label: '처방전', emoji: '📋' },
  { href: '/chat', label: 'AI 상담', emoji: '🤖' },
  { href: '/mypage', label: '마이페이지', emoji: '👤' },
];

export default function AppHeader() {
  const [large, setLarge] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const loggedIn = isLoggedIn();

  const toggleFontSize = () => {
    document.body.classList.toggle('large-text');
    setLarge((prev) => !prev);
  };

  const handleLogout = () => {
    removeToken();
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b-2 border-gray-200">
      <div className="max-w-screen-xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href={loggedIn ? '/dashboard' : '/'}
          className="text-2xl font-extrabold tracking-tight"
          style={{ color: '#4a90e2' }}>
          설리반
        </Link>

        {/* 데스크탑 네비게이션 */}
        {loggedIn && (
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map(({ href, label }) => (
              <Link key={href} href={href}
                className={`px-4 py-2 rounded-xl text-base font-semibold transition-colors ${pathname.startsWith(href) ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:bg-gray-50'}`}>
                {label}
              </Link>
            ))}
          </nav>
        )}

        <div className="flex items-center gap-2">
          <button onClick={toggleFontSize}
            className="text-sm text-gray-500 border border-gray-300 rounded-lg px-3 py-1.5 hover:bg-gray-50"
            aria-label="글씨 크기 조절" aria-pressed={large}>
            가 / 가
          </button>

          {loggedIn ? (
            <>
              <Link href="/prescriptions/upload"
                className="hidden md:block text-base font-bold text-white rounded-xl px-4 py-2"
                style={{ backgroundColor: '#4a90e2' }}>
                처방전 업로드
              </Link>
              <button onClick={handleLogout}
                className="hidden md:block text-base font-semibold text-gray-600 border border-gray-300 rounded-xl px-4 py-2 hover:bg-gray-50">
                로그아웃
              </button>
              {/* 모바일 햄버거 */}
              <button onClick={() => setMenuOpen((v) => !v)}
                className="md:hidden p-2 rounded-lg border border-gray-300"
                aria-label="메뉴">
                ☰
              </button>
            </>
          ) : (
            <>
              <Link href="/login"
                className="text-base font-semibold text-gray-700 border border-gray-300 rounded-xl px-4 py-2 hover:bg-gray-50">
                로그인
              </Link>
              <Link href="/signup"
                className="text-base font-semibold text-white rounded-xl px-4 py-2 hover:opacity-90"
                style={{ backgroundColor: '#4a90e2' }}>
                회원가입
              </Link>
            </>
          )}
        </div>
      </div>

      {/* 모바일 드롭다운 메뉴 */}
      {menuOpen && loggedIn && (
        <div className="md:hidden bg-white border-t border-gray-200 px-4 py-3 flex flex-col gap-1">
          {NAV_ITEMS.map(({ href, label, emoji }) => (
            <Link key={href} href={href} onClick={() => setMenuOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-lg font-semibold ${pathname.startsWith(href) ? 'text-blue-600 bg-blue-50' : 'text-gray-700'}`}>
              <span>{emoji}</span>{label}
            </Link>
          ))}
          <button onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-lg font-semibold text-red-500 mt-1">
            🚪 로그아웃
          </button>
        </div>
      )}
    </header>
  );
}
