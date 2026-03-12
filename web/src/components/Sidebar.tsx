"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

/* ── Sidebar Icons (20×20) ── */
function IconHome() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z" />
      <polyline points="9 21 9 14 15 14 15 21" />
    </svg>
  );
}

function IconPrescription() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <line x1="9" y1="10" x2="15" y2="10" />
      <line x1="9" y1="14" x2="13" y2="14" />
    </svg>
  );
}

function IconGuide() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 5a2 2 0 0 1 2-2h4l2 2 2-2h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5z" />
      <line x1="12" y1="5" x2="12" y2="19" />
    </svg>
  );
}

function IconChat() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" />
    </svg>
  );
}

function IconSettings() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

const iconMap: Record<string, () => React.JSX.Element> = {
  "/dashboard": IconHome,
  "/prescriptions/upload": IconPrescription,
  "/guides": IconGuide,
  "/chat": IconChat,
  "/settings": IconSettings,
};

const menuItems = [
  { href: "/dashboard", label: "대시보드", roles: ["patient", "caregiver"] },
  { href: "/prescriptions/upload", label: "처방전 업로드", roles: ["patient"] },
  { href: "/guides", label: "가이드 내역", roles: ["patient", "caregiver"] },
  { href: "/chat", label: "AI 상담", roles: ["patient", "caregiver"] },
  { href: "/settings", label: "설정", roles: ["patient", "caregiver"] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const role = user?.role?.toLowerCase() || "patient";

  return (
    <aside
      className="hidden md:flex flex-col w-60 border-r min-h-screen p-4"
      style={{ background: 'var(--color-card-bg)', borderColor: 'var(--color-border)' }}
    >
      <nav className="space-y-1 flex-1">
        {menuItems
          .filter((item) => item.roles.includes(role))
          .map((item) => {
            const active = pathname.startsWith(item.href);
            const Icon = iconMap[item.href];
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-4 min-h-[48px] rounded-lg text-sm font-medium transition-colors"
                style={
                  active
                    ? { background: 'var(--color-primary-soft)', color: 'var(--color-primary)', borderLeft: '3px solid var(--color-primary)' }
                    : { color: 'var(--color-text-muted)' }
                }
                onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--color-surface)'; }}
                onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = ''; }}
              >
                {Icon && <Icon />}
                {item.label}
              </Link>
            );
          })}
      </nav>
    </aside>
  );
}
