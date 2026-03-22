"use client";

import Link from "next/link";

/* ── SVG Wave Background (hero-only) ── */
function WaveBackground() {
  return (
    <div className="hero-wave-wrap" aria-hidden="true">
      <svg
        className="hero-wave hero-wave-1"
        viewBox="0 0 1440 320"
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M0,160 C360,260 720,60 1080,160 C1260,210 1380,180 1440,160 L1440,320 L0,320Z"
          fill="var(--color-primary)"
          fillOpacity="0.06"
        />
      </svg>
      <svg
        className="hero-wave hero-wave-2"
        viewBox="0 0 1440 320"
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M0,200 C320,100 640,280 960,160 C1120,100 1320,200 1440,180 L1440,320 L0,320Z"
          fill="var(--color-secondary)"
          fillOpacity="0.05"
        />
      </svg>
      <svg
        className="hero-wave hero-wave-3"
        viewBox="0 0 1440 320"
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M0,240 C480,140 960,280 1440,200 L1440,320 L0,320Z"
          fill="var(--color-primary)"
          fillOpacity="0.04"
        />
      </svg>
    </div>
  );
}

export default function HeroSection() {
  return (
    <section
      className="hero-section relative overflow-hidden py-20 px-4 sm:py-28 sm:px-6 text-center"
      style={{ background: "linear-gradient(168deg, var(--color-surface) 0%, var(--color-bg) 50%, var(--color-primary-pale) 100%)" }}
      aria-label="서비스 소개"
    >
      <WaveBackground />

      <div className="relative z-10 max-w-2xl mx-auto">
        {/* H1 — staggered fade-up */}
        <h1
          className="hero-fade-up font-bold mb-5"
          style={{ color: "var(--color-text)", fontSize: "clamp(1.6rem, 5vw, 2.6rem)", lineHeight: 1.25, animationDelay: "0.1s" }}
        >
          처방전 한 장으로<br />
          <span style={{ color: "var(--color-primary)" }}>AI 복약 가이드</span>를 받으세요
        </h1>

        {/* 부제 — mobile */}
        <p
          aria-hidden="true"
          className="hero-fade-up sm:hidden text-base mb-10 mx-auto"
          style={{ color: "var(--color-text-muted)", maxWidth: "22rem", lineHeight: 1.8, animationDelay: "0.25s" }}
        >
          처방전 업로드 한 번으로<br />
          AI 복약 가이드를 받으세요.
        </p>
        {/* 부제 — desktop */}
        <p
          className="hero-fade-up hidden sm:block text-lg mb-10 mx-auto"
          style={{ color: "var(--color-text-muted)", maxWidth: "34rem", lineHeight: 1.8, animationDelay: "0.25s" }}
        >
          처방전을 업로드하면<br />
          AI가 복약 지침과 주의사항을 알기 쉽게 정리해 드립니다.
        </p>

        {/* CTA */}
        <div className="hero-fade-up" style={{ animationDelay: "0.4s" }}>
          <Link
            href="/signup"
            className="hero-cta inline-flex items-center justify-center px-8 sm:px-10 py-4 rounded-2xl text-white font-semibold cursor-pointer"
            style={{
              backgroundColor: "var(--color-primary)",
              fontSize: "1rem",
              boxShadow: "0 4px 14px rgba(5, 150, 105, 0.25)",
            }}
          >
            지금 바로 시작하세요
          </Link>
        </div>

        {/* 보조 안내 */}
        <p className="hero-fade-up mt-5 text-sm" style={{ color: "var(--color-text-muted)", animationDelay: "0.5s" }}>
          이미 회원이신가요?&nbsp;
          <Link href="/login" className="underline underline-offset-2 hover:opacity-70 transition-opacity" style={{ color: "var(--color-primary)" }}>
            로그인
          </Link>
        </p>
      </div>
    </section>
  );
}
