"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { usePatient } from "@/lib/patient-context";

/* ── Sidebar Icons (24×24, filled) ── */
function IconHome() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
    </svg>
  );
}

function IconPrescription() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM8 13h8v1.5H8V13zm0 3h8v1.5H8V16zm0-6h3v1.5H8V10z"/>
    </svg>
  );
}

function IconGuide() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z"/>
    </svg>
  );
}

function IconChat() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      <path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/>
    </svg>
  );
}

function IconChatHistory() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
    </svg>
  );
}

function IconGuardian() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
    </svg>
  );
}

function IconNotification() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
    </svg>
  );
}

function IconProfile() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
    </svg>
  );
}

function IconProxyProfile() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
    </svg>
  );
}

const topMenuItems = [
  {
    href: "/caregivers",
    label: (role: string) => (role === "guardian" ? "돌봄 대상 관리" : "나의 보호자"),
    roles: ["guardian", "patient"],
    icon: IconGuardian,
  },
  { href: "/dashboard", label: () => "대시보드", roles: ["patient"], icon: IconHome },
  { href: "/prescriptions/upload", label: () => "처방전 업로드", roles: ["patient"], icon: IconPrescription },
  { href: "/guides", label: () => "가이드 내역", roles: ["patient"], icon: IconGuide },
  { href: "/chat", label: () => "AI 상담", roles: ["patient", "guardian"], icon: IconChat },
  { href: "/chat/history", label: () => "상담기록", roles: ["patient", "guardian"], icon: IconChatHistory },
  { href: "/notifications", label: () => "알림센터", roles: ["patient", "guardian"], icon: IconNotification },
  { href: "/proxy-profile", label: () => "돌봄 대상 프로필", roles: ["guardian_proxy"], icon: IconProxyProfile },
];

const bottomMenuItems = [
  { href: "/profile", label: () => "마이페이지", roles: ["patient", "guardian"], icon: IconProfile },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const { isProxyMode } = usePatient();
  const role = user?.role?.toLowerCase() || "patient";

  function renderMenuItem(item: { href: string; label: (role: string) => string; roles: string[]; icon: () => React.JSX.Element }) {
    const active = item.href === "/chat"
      ? pathname === "/chat" || (pathname.startsWith("/chat/") && !pathname.startsWith("/chat/history"))
      : pathname.startsWith(item.href);
    const Icon = item.icon;
    return (
      <Link
        key={item.href}
        href={item.href}
        aria-current={active ? "page" : undefined}
        className="flex items-center gap-3 px-4 min-h-[52px] rounded-xl text-sm font-medium transition-all"
        style={
          active
            ? { background: "var(--color-primary-soft)", color: "var(--color-primary)" }
            : { color: "var(--color-text-muted)" }
        }
        onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = "var(--color-surface)"; }}
        onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = ""; }}
      >
        <Icon />
        {item.label(role)}
      </Link>
    );
  }

  return (
    <aside
      className="hidden md:flex flex-col w-60 min-h-screen p-4"
      style={{ background: "var(--color-card-bg)", boxShadow: "var(--shadow-sm)" }}
    >
      <nav className="flex-1 space-y-1" aria-label="메인 네비게이션">
        {topMenuItems
          .filter((item) => {
            if (item.roles.includes("guardian_proxy")) return isProxyMode;
            if (isProxyMode) return item.roles.includes("patient") || item.roles.includes(role);
            return item.roles.includes(role);
          })
          .map(renderMenuItem)}
      </nav>
      <hr style={{ borderColor: "var(--color-surface-alt)" }} className="my-2" />
      <nav className="space-y-1 py-2">
        {bottomMenuItems.filter((item) => item.roles.includes(role)).map(renderMenuItem)}
      </nav>
    </aside>
  );
}
