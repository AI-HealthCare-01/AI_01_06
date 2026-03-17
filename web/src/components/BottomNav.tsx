"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { usePatient } from "@/lib/patient-context";

/* ── Nav Icons (24×24, stroke-based) ── */
function IconHome({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}>
      <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z" />
      <polyline points="9 21 9 14 15 14 15 21" />
    </svg>
  );
}

function IconPrescription({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}>
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <path d="M9 3V1.5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 1.5V3" />
      <line x1="9" y1="10" x2="15" y2="10" />
      <line x1="9" y1="14" x2="13" y2="14" />
    </svg>
  );
}

function IconGuide({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}>
      <path d="M4 5a2 2 0 0 1 2-2h4l2 2 2-2h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5z" />
      <line x1="12" y1="5" x2="12" y2="19" />
    </svg>
  );
}

function IconChat({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" />
      <line x1="8" y1="9" x2="16" y2="9" />
      <line x1="8" y1="13" x2="13" y2="13" />
    </svg>
  );
}

function IconChatHistory({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" />
      <circle cx="12" cy="10" r="3" />
      <polyline points="12 8 12 10 13.5 11" />
    </svg>
  );
}

function IconGuardian({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <circle cx="12" cy="10" r="2" />
      <path d="M8 16c0-2.2 1.8-4 4-4s4 1.8 4 4" />
    </svg>
  );
}

function IconProfile({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
    </svg>
  );
}

const menuItems = [
  {
    href: "/caregivers",
    label: (role: string) => (role === "guardian" ? "돌봄 대상" : "나의 보호자"),
    icon: IconGuardian,
    roles: ["guardian", "patient"],
  },
  { href: "/dashboard", label: () => "홈", icon: IconHome, roles: ["patient"] },
  { href: "/prescriptions/upload", label: () => "처방전", icon: IconPrescription, roles: ["patient"] },
  { href: "/guides", label: () => "가이드", icon: IconGuide, roles: ["patient"] },
  { href: "/chat", label: () => "AI 상담", icon: IconChat, roles: ["patient"] },
  { href: "/chat/history", label: () => "상담기록", icon: IconChatHistory, roles: ["guardian"] },
  { href: "/profile", label: () => "마이페이지", icon: IconProfile, roles: ["patient", "guardian"] },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const { isProxyMode } = usePatient();
  const role = user?.role?.toLowerCase() || "patient";

  const visibleItems = menuItems.filter((item) => {
    if (isProxyMode) {
      return (item.roles.includes("patient") || item.href === "/chat/history") && item.href !== "/caregivers";
    }
    return item.roles.includes(role);
  });

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 md:hidden pb-safe"
      style={{ background: "var(--color-card-bg)", borderTop: "1px solid var(--color-border)" }}
      aria-label="모바일 메인 네비게이션"
    >
      <div className="flex items-center justify-around h-16">
        {visibleItems.map((item) => {
          const active = item.href === "/chat"
            ? pathname === "/chat" || (pathname.startsWith("/chat/") && !pathname.startsWith("/chat/history"))
            : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label(role)}
              aria-current={active ? "page" : undefined}
              className="flex flex-col items-center justify-center gap-0.5 min-w-[48px] min-h-[48px] px-2"
            >
              <Icon active={active} />
              <span
                className="text-[10px] font-medium leading-tight"
                style={{ color: active ? "var(--color-primary)" : "var(--color-text-muted)" }}
              >
                {item.label(role)}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
