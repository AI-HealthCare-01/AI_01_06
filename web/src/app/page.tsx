"use client";

import Link from "next/link";
import Header from "@/components/Header";

/* ══════════════════════════════════════
   SVG 아이콘 — filled style · 고령층 가독성 최적화
══════════════════════════════════════ */
function IconUpload() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM8 13h8v1.5H8V13zm0 3h8v1.5H8V16zm0-6h3v1.5H8V10z" />
    </svg>
  );
}
function IconGuide() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z" />
    </svg>
  );
}
function IconChat() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
      <path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z" />
    </svg>
  );
}
function IconDashboard() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M3 3h8v8H3zm10 0h8v8h-8zM3 13h8v8H3zm10 0h8v8h-8z" />
    </svg>
  );
}
function IconFamily() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
    </svg>
  );
}
function IconBell() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
    </svg>
  );
}
function IconShield() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z" />
    </svg>
  );
}
function IconCheck() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

/* ── 데스크톱 스텝 간 화살표 ── */
function StepArrow() {
  return (
    <div className="hidden sm:flex items-center justify-center" aria-hidden="true">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-border)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="5" y1="12" x2="19" y2="12" />
        <polyline points="12 5 19 12 12 19" />
      </svg>
    </div>
  );
}

/* ══════════════════════════════════════
   데이터
══════════════════════════════════════ */
const steps = [
  { num: "01", title: "처방전 업로드", desc: "사진이나 파일로 처방전을 올려주세요.", icon: <IconUpload />, label: "업로드 아이콘" },
  { num: "02", title: "AI 가이드 생성", desc: "AI가 맞춤형 복약 지침을 자동으로 만들어 드립니다.", icon: <IconGuide />, label: "가이드 문서 아이콘" },
  { num: "03", title: "AI 상담",       desc: "궁금한 점을 AI와 실시간으로 상담하세요.", icon: <IconChat />, label: "상담 아이콘" },
];

const features = [
  { title: "환자 대시보드", desc: "복약 일정과 가이드를 한눈에 확인", icon: <IconDashboard /> },
  { title: "보호자 모드",  desc: "가족의 복약 현황을 함께 관리",     icon: <IconFamily /> },
  { title: "복약 알림",   desc: "시간에 맞춰 복약 알림 제공",       icon: <IconBell /> },
  { title: "안전한 보안", desc: "개인 정보를 안전하게 보호",         icon: <IconShield /> },
];

const targets = [
  "여러 가지 약을 복용하시는 어르신",
  "부모님의 약 관리가 걱정되시는 보호자",
  "약 복용 시간과 방법이 헷갈리시는 분",
  "병원 진료 시간이 짧아 자세히 못 여쭤보신 분",
];

/* ══════════════════════════════════════
   페이지
══════════════════════════════════════ */
export default function LandingPage() {
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

        {/* ── ① Hero ─────────────────────────────── */}
        <section
          className="py-16 px-4 sm:py-20 sm:px-6 text-center animate-section"
          style={{ background: "linear-gradient(160deg, var(--color-surface) 0%, var(--color-bg) 60%)" }}
          aria-label="서비스 소개"
        >
          <div className="max-w-2xl mx-auto">

            {/* H1 */}
            <h1
              className="font-bold mb-5"
              style={{ color: "var(--color-text)", fontSize: "clamp(1.6rem, 5vw, 2.6rem)", lineHeight: 1.25 }}
            >
              처방전 한 장으로<br />
              <span style={{ color: "var(--color-primary)" }}>AI 복약 가이드</span>를 받으세요
            </h1>

            {/* 부제 — 모바일: 짧은 문구(2줄), 데스크탑: 전체 문구(2줄) */}
            <p
              aria-hidden="true"
              className="sm:hidden text-base mb-8 mx-auto"
              style={{ color: "var(--color-text-muted)", maxWidth: "22rem", lineHeight: 1.8 }}
            >
              처방전 업로드 한 번으로<br />
              AI 복약 가이드를 받으세요.
            </p>
            <p
              className="hidden sm:block text-lg mb-8 mx-auto"
              style={{ color: "var(--color-text-muted)", maxWidth: "34rem", lineHeight: 1.8 }}
            >
              처방전을 업로드하면<br />
              AI가 복약 지침과 주의사항을 알기 쉽게 정리해 드립니다.
            </p>

            {/* CTA */}
            <Link
              href="/signup"
              className="cta-hover inline-flex items-center justify-center px-8 sm:px-10 py-4 rounded-2xl text-white font-semibold cursor-pointer"
              style={{
                backgroundColor: "var(--color-primary)",
                fontSize: "1rem",
                boxShadow: "0 4px 14px rgba(5, 150, 105, 0.25)",
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = "var(--color-primary-hover)")}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = "var(--color-primary)")}
            >
              지금 바로 시작하세요
            </Link>

            {/* 보조 안내 */}
            <p className="mt-4 text-sm" style={{ color: "var(--color-text-muted)" }}>
              이미 회원이신가요?&nbsp;
              <Link href="/login" className="underline underline-offset-2 hover:opacity-70 transition-opacity" style={{ color: "var(--color-primary)" }}>
                로그인
              </Link>
            </p>
          </div>
        </section>

        {/* ── ② 이용방법 ──────────────────────────── */}
        <section
          className="py-16 px-4 sm:py-20 sm:px-6 animate-section"
          style={{ backgroundColor: "var(--color-surface)" }}
          aria-labelledby="how-title"
        >
          <div className="max-w-5xl mx-auto">
            <h2
              id="how-title"
              className="section-heading font-bold text-center mb-12"
              style={{ color: "var(--color-text)", fontSize: "clamp(1.25rem, 3vw, 1.75rem)" }}
            >
              이용방법
            </h2>

            {/* Steps — 모바일: 세로 카드 / 데스크톱: 3열 with arrows */}
            <div className="flex flex-col sm:grid gap-6 sm:gap-0 items-stretch" style={{ gridTemplateColumns: '1fr 2rem 1fr 2rem 1fr' }}>
              {steps.map((s, idx) => (
                <div key={s.num} className="contents">
                  {/* 카드 */}
                  <div
                    className="card-hover relative flex sm:flex-col sm:items-center sm:text-center items-start gap-4 sm:gap-0 p-5 sm:p-6 rounded-2xl border-2"
                    style={{
                      backgroundColor: "var(--color-card-bg)",
                      borderColor: "var(--color-border)",
                      boxShadow: "0 2px 8px rgba(45, 42, 38, 0.06)",
                    }}
                  >
                    {/* 아이콘 박스 */}
                    <div
                      className="shrink-0 w-16 h-16 sm:w-20 sm:h-20 rounded-full flex items-center justify-center sm:mb-4"
                      style={{ backgroundColor: "var(--color-primary-soft)", color: "var(--color-primary)" }}
                      role="img"
                      aria-label={s.label}
                    >
                      {s.icon}
                    </div>

                    {/* 텍스트 */}
                    <div>
                      <span
                        className="inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold mb-2"
                        style={{ backgroundColor: "var(--color-primary)", color: "#fff" }}
                      >
                        {s.num}
                      </span>
                      <h3
                        className="font-bold text-lg mb-1"
                        style={{ color: "var(--color-text)" }}
                      >
                        {s.title}
                      </h3>
                      <p
                        className="text-sm leading-relaxed"
                        style={{ color: "var(--color-text-muted)" }}
                      >
                        {s.desc}
                      </p>
                    </div>
                  </div>

                  {/* 데스크톱 화살표 (마지막 아이템 제외) */}
                  {idx < steps.length - 1 && <StepArrow />}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── ③ 기능 안내 ─────────────────────────── */}
        <section
          className="py-16 px-4 sm:py-20 sm:px-6 animate-section"
          style={{ backgroundColor: "var(--color-bg)" }}
          aria-labelledby="feature-title"
        >
          <div className="max-w-5xl mx-auto">
            <h2
              id="feature-title"
              className="section-heading font-bold text-center mb-12"
              style={{ color: "var(--color-text)", fontSize: "clamp(1.25rem, 3vw, 1.75rem)" }}
            >
              기능 안내
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {features.map((f) => (
                <div
                  key={f.title}
                  className="card-hover flex items-start gap-4 p-5 sm:p-6 rounded-2xl border-2"
                  style={{
                    backgroundColor: "var(--color-card-bg)",
                    borderColor: "var(--color-border)",
                    boxShadow: "0 2px 8px rgba(45, 42, 38, 0.06)",
                  }}
                >
                  <div
                    className="shrink-0 w-14 h-14 rounded-xl flex items-center justify-center"
                    style={{ backgroundColor: "var(--color-primary-soft)", color: "var(--color-primary)" }}
                  >
                    {f.icon}
                  </div>
                  <div>
                    <h3 className="font-bold text-base mb-1" style={{ color: "var(--color-text)" }}>
                      {f.title}
                    </h3>
                    <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
                      {f.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── ④ 이런분께 ──────────────────────────── */}
        <section
          className="py-16 px-4 sm:py-20 sm:px-6 animate-section"
          style={{ backgroundColor: "var(--color-surface-alt)" }}
          aria-labelledby="target-title"
        >
          <div className="max-w-2xl mx-auto">
            <h2
              id="target-title"
              className="section-heading font-bold text-center mb-10"
              style={{ color: "var(--color-text)", fontSize: "clamp(1.25rem, 3vw, 1.75rem)" }}
            >
              이런 분께 도움이 됩니다
            </h2>

            <ul className="space-y-4" role="list">
              {targets.map((t) => (
                <li
                  key={t}
                  className="flex items-center gap-4 px-6 py-5 rounded-xl border-2"
                  style={{
                    backgroundColor: "var(--color-card-bg)",
                    borderColor: "var(--color-border)",
                  }}
                >
                  <span
                    className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: "var(--color-primary)", color: "#fff" }}
                  >
                    <IconCheck />
                  </span>
                  <span className="text-base font-medium" style={{ color: "var(--color-text)" }}>
                    {t}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>

      </main>

      {/* ── ⑤ Footer ─────────────────────────────── */}
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
    </div>
  );
}
