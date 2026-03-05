'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV = [
  { href: '/dashboard', label: '홈', emoji: '🏠' },
  { href: '/prescriptions/list', label: '처방전', emoji: '📋' },
  { href: '/prescriptions/upload', label: '업로드', emoji: '➕' },
  { href: '/chat', label: 'AI 상담', emoji: '🤖' },
  { href: '/mypage', label: '내 정보', emoji: '👤' },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-gray-200 flex">
      {NAV.map(({ href, label, emoji }) => {
        const active = pathname.startsWith(href);
        return (
          <Link key={href} href={href}
            className={`flex-1 flex flex-col items-center justify-center py-3 gap-1 text-xs font-semibold transition-colors ${active ? 'text-blue-600' : 'text-gray-400'}`}>
            <span className="text-2xl">{emoji}</span>
            <span>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
