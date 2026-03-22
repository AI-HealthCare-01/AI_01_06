"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, pollNotificationCount } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

type FontSize = "normal" | "large";

/* ── 로고 심볼 (&) — rounded modern stroke ── */
function LogoMark() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="var(--color-primary)" />
      <path
        d="M22 25C19 22 16.5 19 14.5 17C12.5 14.5 13 10 15.5 9.5C18 9 19.5 10.5 19 12.5C18.5 14.5 16 16 14.5 17C13 18 10 21 10 23C10 25 12 26 14.5 26C17 26 20 24.5 22 25"
        stroke="white"
        strokeWidth="2.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}

/* ── 모바일 아이콘 ── */
function IconLogin() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
      <polyline points="10 17 15 12 10 7" />
      <line x1="15" y1="12" x2="3" y2="12" />
    </svg>
  );
}

function IconSignup() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <line x1="19" y1="8" x2="19" y2="14" />
      <line x1="22" y1="11" x2="16" y2="11" />
    </svg>
  );
}

function IconLogout() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

function IconBell() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

export default function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [fontSize, setFontSize] = useState<FontSize>("large");
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!user) { setUnreadCount(0); return; }

    const abortCtrl = new AbortController();
    let pollCtrl: AbortController | undefined;

    api.checkMissed().finally(() => {
      if (abortCtrl.signal.aborted) return;
      pollCtrl = pollNotificationCount(
        (count) => setUnreadCount(count),
        30000,
      );
    });

    return () => {
      abortCtrl.abort();
      pollCtrl?.abort();
    };
  }, [user]);

  useEffect(() => {
    const saved = (localStorage.getItem("fontSize") as FontSize) ?? "large";
    setFontSize(saved);
    document.documentElement.setAttribute("data-font-size", saved);
  }, []);

  useEffect(() => {
    const handler = (e: Event) => {
      const size = (e as CustomEvent).detail.size as FontSize;
      setFontSize(size);
    };
    window.addEventListener("fontSizeChanged", handler);
    return () => window.removeEventListener("fontSizeChanged", handler);
  }, []);

  const toggleFontSize = (size: FontSize) => {
    setFontSize(size);
    localStorage.setItem("fontSize", size);
    document.documentElement.setAttribute("data-font-size", size);
    window.dispatchEvent(new CustomEvent("fontSizeChanged", { detail: { size } }));
    if (user) {
      api.updateMe({ font_size_mode: size }).catch(() => {});
    }
  };

  return (
    <header
      className="sticky top-0 z-50"
      style={{ backgroundColor: "var(--color-card-bg)", boxShadow: "var(--shadow-sm)" }}
    >
      <div className="h-14 sm:h-16 px-4 sm:px-6 flex items-center justify-between gap-3">

        {/* ── 로고 ── */}
        <Link
          href={user ? "/dashboard" : "/"}
          className="flex items-center gap-2.5 shrink-0"
          aria-label="Sullivan 홈으로"
        >
          <LogoMark />
          <span
            className="font-bold text-base sm:text-lg leading-none"
            style={{ color: "var(--color-primary)", fontFamily: "'Gowun Batang', serif" }}
          >
            Sullivan
          </span>
        </Link>

        {/* ── 우측: 벨 + 폰트토글 + 인증 ── */}
        <div className="flex items-center gap-2">

          {/* 알림 벨 (로그인 시만) */}
          {user && (
            <Link
              href="/notifications"
              aria-label={unreadCount > 0 ? `읽지 않은 알림 ${unreadCount}건` : "알림센터"}
              className="relative w-10 h-10 flex items-center justify-center rounded-lg transition-colors"
              style={{ color: "var(--color-text-muted)" }}
            >
              <IconBell />
              {unreadCount > 0 && (
                <span
                  className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full text-[10px] font-bold"
                  style={{ backgroundColor: "var(--color-danger)", color: "#fff" }}
                  aria-hidden="true"
                >
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </Link>
          )}

          {/* 글씨 크기 2단계 토글 */}
          <div
            className="flex items-center rounded-lg border overflow-hidden"
            style={{ borderColor: "var(--color-border)" }}
            role="group"
            aria-label="글씨 크기 설정"
          >
            <button
              onClick={() => toggleFontSize("normal")}
              aria-pressed={fontSize === "normal"}
              aria-label="작은 글씨로 보기"
              className="w-10 h-10 flex items-center justify-center transition-colors cursor-pointer"
              style={
                fontSize === "normal"
                  ? { backgroundColor: "var(--color-primary)", color: "#fff" }
                  : { color: "var(--color-text-muted)" }
              }
            >
              <span style={{ fontSize: "11px", fontWeight: 700, lineHeight: 1 }}>가</span>
            </button>
            <div className="w-px h-5" style={{ backgroundColor: "var(--color-border)" }} aria-hidden="true" />
            <button
              onClick={() => toggleFontSize("large")}
              aria-pressed={fontSize === "large"}
              aria-label="큰 글씨로 보기"
              className="w-10 h-10 flex items-center justify-center transition-colors cursor-pointer"
              style={
                fontSize === "large"
                  ? { backgroundColor: "var(--color-primary)", color: "#fff" }
                  : { color: "var(--color-text-muted)" }
              }
            >
              <span style={{ fontSize: "15px", fontWeight: 700, lineHeight: 1 }}>가</span>
            </button>
          </div>

          {/* ── 인증 버튼 ── */}
          {user ? (
            <div className="flex items-center gap-1.5">
              {/* 닉네임: sm 이상 표시, md 이상 넓게 */}
              <span
                className="hidden sm:block text-sm px-2 truncate max-w-[72px] md:max-w-[120px] lg:max-w-[160px]"
                style={{ color: "var(--color-text-muted)" }}
              >
                {user.nickname}
              </span>
              {/* 로그아웃: 모바일 아이콘 / sm+ 텍스트 */}
              <button
                onClick={() => { logout(); router.push("/"); }}
                aria-label="로그아웃"
                className="w-10 h-10 sm:w-auto sm:h-10 sm:px-4 flex items-center justify-center gap-2 rounded-lg border text-sm font-medium transition-colors cursor-pointer"
                style={{ borderColor: "var(--color-border)", color: "var(--color-text-muted)" }}
              >
                <IconLogout />
                <span className="hidden sm:inline">로그아웃</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              {/* 로그인: 모바일 아이콘 / sm+ 텍스트 */}
              <Link
                href="/login"
                aria-label="로그인"
                className="w-10 h-10 sm:w-auto sm:h-10 sm:px-4 flex items-center justify-center gap-2 rounded-lg border text-sm font-medium transition-colors cursor-pointer"
                style={{ borderColor: "var(--color-border)", color: "var(--color-text-muted)" }}
              >
                <IconLogin />
                <span className="hidden sm:inline">로그인</span>
              </Link>
              {/* 회원가입: 모바일 아이콘 / sm+ 텍스트 */}
              <Link
                href="/signup"
                aria-label="회원가입"
                className="w-10 h-10 sm:w-auto sm:h-10 sm:px-4 flex items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-colors cursor-pointer"
                style={{ backgroundColor: "var(--color-primary)", color: "#fff" }}
                onMouseEnter={e => (e.currentTarget.style.backgroundColor = "var(--color-primary-hover)")}
                onMouseLeave={e => (e.currentTarget.style.backgroundColor = "var(--color-primary)")}
              >
                <IconSignup />
                <span className="hidden sm:inline">회원가입</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
