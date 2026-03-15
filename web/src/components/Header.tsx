"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

type FontSize = "normal" | "large";

/* ── 로고 심볼 ── */
function LogoMark() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#0D7C66" />
      <path d="M14 8h4v6h6v4h-6v6h-4v-6H8v-4h6V8z" fill="white" />
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

export default function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [fontSize, setFontSize] = useState<FontSize>("large");

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
      className="sticky top-0 z-50 border-b"
      style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-bg)" }}
    >
      <div className="h-14 sm:h-16 px-4 sm:px-6 flex items-center justify-between gap-3">

        {/* ── 로고 ── */}
        <Link
          href={user ? "/dashboard" : "/"}
          className="flex items-center gap-2.5 shrink-0"
          aria-label="Project & Sullivan 홈으로"
        >
          <LogoMark />
          <span
            className="font-bold text-base sm:text-lg leading-none"
            style={{ color: "var(--color-primary)", fontFamily: "'Gowun Batang', serif" }}
          >
            <span className="hidden sm:inline">Project &amp; </span>Sullivan
          </span>
        </Link>

        {/* ── 우측: 폰트토글 + 인증 ── */}
        <div className="flex items-center gap-2">

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
              className="w-9 h-9 flex items-center justify-center transition-colors cursor-pointer"
              style={
                fontSize === "normal"
                  ? { backgroundColor: "var(--color-primary)", color: "#fff" }
                  : { color: "var(--color-text-muted)" }
              }
            >
              <span style={{ fontSize: "11px", fontWeight: 700, lineHeight: 1 }}>가</span>
            </button>
            <div className="w-px h-4" style={{ backgroundColor: "var(--color-border)" }} aria-hidden="true" />
            <button
              onClick={() => toggleFontSize("large")}
              aria-pressed={fontSize === "large"}
              aria-label="큰 글씨로 보기"
              className="w-9 h-9 flex items-center justify-center transition-colors cursor-pointer"
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
              {/* 닉네임: md 이상에서만 표시 */}
              <span
                className="hidden md:block text-sm px-2 truncate max-w-[80px]"
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
