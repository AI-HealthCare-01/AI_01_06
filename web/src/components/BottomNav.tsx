"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { usePatient } from "@/lib/patient-context";

/* ── Nav Icons (24×24, filled) ── */
function IconHome({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-primary)" : "var(--color-text-muted)"}>
      <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
    </svg>
  );
}

function IconPrescription({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-primary)" : "var(--color-text-muted)"}>
      <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM8 13h8v1.5H8V13zm0 3h8v1.5H8V16zm0-6h3v1.5H8V10z"/>
    </svg>
  );
}

function IconGuide({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-primary)" : "var(--color-text-muted)"}>
      <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z"/>
    </svg>
  );
}

function IconChat({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-primary)" : "var(--color-text-muted)"}>
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      <path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/>
    </svg>
  );
}

function IconChatHistory({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-primary)" : "var(--color-text-muted)"}>
      <path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
    </svg>
  );
}

function IconGuardian({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-primary)" : "var(--color-text-muted)"}>
      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
    </svg>
  );
}

function IconProfile({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-primary)" : "var(--color-text-muted)"}>
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
    </svg>
  );
}

const menuItems = [
  { href: "/caregivers", label: (_role: string) => "돌봄 대상", icon: IconGuardian, roles: ["guardian"] },
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

  const proxyPaths = ["/dashboard", "/prescriptions/upload", "/guides", "/chat/history"];
  const visibleItems = menuItems.filter((item) => {
    if (isProxyMode) return proxyPaths.includes(item.href);
    return item.roles.includes(role);
  });

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 md:hidden pb-safe"
      style={{ background: "var(--color-card-bg)", boxShadow: "0 -1px 4px rgba(16, 24, 40, 0.06)" }}
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
                className="text-[10px] font-semibold leading-tight"
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
