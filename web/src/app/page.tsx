"use client";

import { useState, useEffect } from "react";
import Header from "@/components/Header";
import HeroSection from "@/components/landing/HeroSection";
import FlowSection from "@/components/landing/FlowSection";
import DemoCarouselSection from "@/components/landing/DemoCarouselSection";

export default function LandingPage() {
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => setShowScrollTop(window.scrollY > 300);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-dvh" style={{ backgroundColor: "var(--color-bg)" }}>

      {/* Skip Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:rounded-lg focus:text-sm focus:text-white focus:shadow-lg"
        style={{ backgroundColor: "var(--color-primary)" }}
      >
        본문으로 바로가기
      </a>

      <Header />

      <main id="main-content">
        <HeroSection />
        <FlowSection />
        <DemoCarouselSection />
      </main>

      {/* ── Footer ─────────────────────────────── */}
      <footer style={{ backgroundColor: "#2D2A26" }}>
        <div
          className="max-w-5xl mx-auto px-4 sm:px-6 pt-2"
          style={{ borderTop: "3px solid var(--color-primary)" }}
        />
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-12 flex flex-col sm:flex-row justify-between gap-8">

          <div>
            <p
              className="font-bold text-lg mb-1 text-white"
              style={{ fontFamily: "'Gowun Batang', serif" }}
            >
              Sullivan
            </p>
            <p className="text-sm" style={{ color: "#A8A29E" }}>AI 복약 가이드 서비스</p>
          </div>

          <div>
            <p className="font-semibold mb-2 text-white text-sm">고객지원</p>
            <p className="text-sm" style={{ color: "#A8A29E" }}>전화: 000-000-0000</p>
            <p className="text-sm" style={{ color: "#A8A29E" }}>이메일: support@sullivan.com</p>
          </div>

          <div>
            <p className="font-semibold mb-2 text-white text-sm">법적 고지 안내</p>
            <p className="text-sm cursor-pointer hover:text-white transition-colors" style={{ color: "#A8A29E" }}>
              개인정보처리안내
            </p>
            <p className="text-sm cursor-pointer hover:text-white transition-colors" style={{ color: "#A8A29E" }}>
              이용안내
            </p>
          </div>
        </div>

        <div
          className="max-w-5xl mx-auto px-4 sm:px-6 py-4 border-t"
          style={{ borderColor: "#3D3A36" }}
        >
          <p className="text-xs" style={{ color: "#78716C" }}>
            © 2025 Sullivan. All rights reserved.
          </p>
        </div>
      </footer>

      {/* ── Scroll to Top ── */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        className="fixed z-30 w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300"
        style={{
          bottom: "2rem",
          right: "1.5rem",
          backgroundColor: "var(--color-primary)",
          boxShadow: "0 4px 12px rgba(5, 150, 105, 0.3)",
          opacity: showScrollTop ? 1 : 0,
          pointerEvents: showScrollTop ? "auto" : "none",
          transform: showScrollTop ? "translateY(0)" : "translateY(12px)",
        }}
        aria-label="페이지 최상단으로 이동"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="18 15 12 9 6 15" />
        </svg>
      </button>
    </div>
  );
}
