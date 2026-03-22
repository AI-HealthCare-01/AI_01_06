"use client";

import Link from "next/link";

export default function CTASection() {
  return (
    <section
      className="cta-section relative overflow-hidden py-20 px-4 sm:py-24 sm:px-6 animate-section"
      aria-label="시작하기"
    >
      {/* Subtle glow orbs */}
      <div className="cta-glow cta-glow-1" aria-hidden="true" />
      <div className="cta-glow cta-glow-2" aria-hidden="true" />

      <div className="relative z-10 max-w-2xl mx-auto text-center">
        <h2
          className="font-bold mb-4"
          style={{ color: "var(--color-text)", fontSize: "clamp(1.4rem, 3.5vw, 1.9rem)" }}
        >
          지금 바로 시작해 보세요
        </h2>

        {/* Absorbed target audience lines */}
        <div className="space-y-1 mb-10">
          <p className="text-sm sm:text-base" style={{ color: "var(--color-text-muted)" }}>
            여러 약을 드시는 어르신부터, 부모님 약이 걱정되는 보호자까지.
          </p>
          <p className="text-sm sm:text-base" style={{ color: "var(--color-text-muted)" }}>
            처방전 한 장이면 복약 관리가 쉬워집니다.
          </p>
        </div>

        <Link
          href="/signup"
          className="hero-cta inline-flex items-center justify-center px-10 sm:px-12 py-4 rounded-2xl text-white font-semibold cursor-pointer text-base sm:text-lg"
          style={{
            backgroundColor: "var(--color-primary)",
            boxShadow: "0 4px 20px rgba(5, 150, 105, 0.3)",
          }}
        >
          무료로 시작하기
        </Link>

        <p className="mt-5 text-sm" style={{ color: "var(--color-text-muted)" }}>
          가입 후 바로 이용할 수 있습니다
        </p>
      </div>
    </section>
  );
}
