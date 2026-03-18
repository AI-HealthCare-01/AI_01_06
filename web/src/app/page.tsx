"use client";

import Link from "next/link";
import Header from "@/components/Header";

/* ══════════════════════════════════════
   SVG 아이콘 — 고령층 가독성 최적화
   stroke 2.5px · 40px 사이즈
══════════════════════════════════════ */
function IconUpload() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="12" y1="16" x2="12" y2="4" />
      <polyline points="7 9 12 4 17 9" />
      <path d="M4 20h16" />
    </svg>
  );
}
function IconGuide() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <polyline points="9 15 11 17 15 12" />
    </svg>
  );
}
function IconChat() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <line x1="8" y1="10" x2="16" y2="10" />
      <line x1="8" y1="14" x2="12" y2="14" />
    </svg>
  );
}
function IconDashboard() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}
function IconFamily() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
function IconBell() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}
function IconShield() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
function IconCheck() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
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

            {/* 서비스 뱃지 */}
            <p
              className="inline-block text-xs font-semibold px-4 py-1.5 rounded-full mb-6"
              style={{ backgroundColor: "#FDEBD0", color: "var(--color-accent)" }}
            >
              AI 맞춤형 복약 가이드 서비스
            </p>

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
                backgroundColor: "var(--color-cta)",
                fontSize: "1rem",
                boxShadow: "0 4px 14px rgba(217, 119, 6, 0.3)",
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = "var(--color-cta-hover)")}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = "var(--color-cta)")}
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
                        style={{ backgroundColor: "var(--color-accent)", color: "#fff" }}
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
              Project &amp; Sullivan
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
            © 2025 Project &amp; Sullivan. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
