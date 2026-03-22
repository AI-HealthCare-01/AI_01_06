"use client";

import { useState, useCallback } from "react";
import Image from "next/image";

const demos = [
  {
    id: "ocr",
    title: "처방전 자동 인식",
    desc: "처방전을 촬영하면 AI가 약 이름, 용량, 복용법을 자동으로 인식합니다.",
    src: "/landing/demo-ocr.png",
  },
  {
    id: "guide",
    title: "맞춤 복약 가이드",
    desc: "복용법, 주의사항, 부작용까지 한눈에 보기 쉽게 정리해 드립니다.",
    src: "/landing/demo-guide.png",
  },
  {
    id: "chat",
    title: "AI 실시간 상담",
    desc: "궁금한 점을 언제든 AI에게 물어보세요. 24시간 상담 가능합니다.",
    src: "/landing/demo-chat.png",
  },
];

/* ── Arrow icon ── */
function ArrowIcon({ direction }: { direction: "left" | "right" }) {
  const points = direction === "left" ? "15 18 9 12 15 6" : "9 18 15 12 9 6";
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points={points} />
    </svg>
  );
}

export default function DemoCarouselSection() {
  const [activeIdx, setActiveIdx] = useState(0);

  const goTo = useCallback((idx: number) => {
    setActiveIdx(idx);
  }, []);

  const goPrev = useCallback(() => {
    setActiveIdx((prev) => (prev === 0 ? demos.length - 1 : prev - 1));
  }, []);

  const goNext = useCallback(() => {
    setActiveIdx((prev) => (prev === demos.length - 1 ? 0 : prev + 1));
  }, []);

  const active = demos[activeIdx];

  return (
    <section
      className="py-16 px-4 sm:py-20 sm:px-6 animate-section"
      style={{ backgroundColor: "var(--color-bg)" }}
      aria-labelledby="demo-title"
    >
      <div className="max-w-4xl mx-auto">
        <h2
          id="demo-title"
          className="section-heading font-bold text-center mb-4"
          style={{ color: "var(--color-text)", fontSize: "clamp(1.25rem, 3vw, 1.75rem)" }}
        >
          이런 서비스를 제공해요
        </h2>
        <p className="text-center text-sm mb-10" style={{ color: "var(--color-text-muted)" }}>
          실제 화면을 확인해 보세요
        </p>

        {/* Tab buttons — wrap allowed on mobile */}
        <div className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-8">
          {demos.map((d, idx) => (
            <button
              key={d.id}
              onClick={() => goTo(idx)}
              className="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-sm font-semibold transition-all"
              style={
                idx === activeIdx
                  ? { background: "var(--color-primary)", color: "#fff", boxShadow: "0 2px 8px rgba(5,150,105,0.2)" }
                  : { background: "var(--color-surface)", color: "var(--color-text-muted)" }
              }
            >
              {d.title}
            </button>
          ))}
        </div>

        {/* Demo card */}
        <div className="relative">
          {/* Desktop-only side arrows */}
          <button
            onClick={goPrev}
            className="demo-nav-btn hidden sm:flex absolute -left-5 top-1/2 -translate-y-1/2 z-10 w-11 h-11 rounded-full items-center justify-center"
            style={{ background: "var(--color-card-bg)", border: "1.5px solid var(--color-border)", boxShadow: "var(--shadow-md)" }}
            aria-label="이전 데모"
          >
            <ArrowIcon direction="left" />
          </button>
          <button
            onClick={goNext}
            className="demo-nav-btn hidden sm:flex absolute -right-5 top-1/2 -translate-y-1/2 z-10 w-11 h-11 rounded-full items-center justify-center"
            style={{ background: "var(--color-card-bg)", border: "1.5px solid var(--color-border)", boxShadow: "var(--shadow-md)" }}
            aria-label="다음 데모"
          >
            <ArrowIcon direction="right" />
          </button>

          {/* Card frame */}
          <div
            className="demo-card mx-auto rounded-2xl overflow-hidden"
            style={{
              background: "var(--color-surface)",
              border: "1.5px solid var(--color-border)",
              boxShadow: "0 8px 30px rgba(5, 150, 105, 0.08), 0 2px 8px rgba(0,0,0,0.04)",
              maxWidth: "420px",
            }}
          >
            {/* Image container — contain, no crop, stable height */}
            <div
              className="relative w-full flex items-center justify-center"
              style={{ height: "clamp(420px, 60vw, 560px)", padding: "12px 12px 0" }}
            >
              <Image
                key={active.id}
                src={active.src}
                alt={`${active.title} 데모 화면`}
                fill
                className="object-contain demo-image-fade"
                sizes="(max-width: 640px) 85vw, 420px"
                style={{ padding: "12px 12px 0 12px" }}
                priority={activeIdx === 0}
              />
            </div>

            {/* Text area */}
            <div className="p-5 sm:p-6 text-center" style={{ background: "var(--color-card-bg)", borderTop: "1px solid var(--color-border)" }}>
              <h3 className="font-bold text-base mb-1" style={{ color: "var(--color-text)" }}>
                {active.title}
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
                {active.desc}
              </p>
            </div>
          </div>
        </div>

        {/* Mobile arrows + dot indicators */}
        <div className="flex justify-center items-center gap-4 mt-6">
          {/* Mobile prev arrow */}
          <button
            onClick={goPrev}
            className="demo-nav-btn sm:hidden w-9 h-9 rounded-full flex items-center justify-center"
            style={{ background: "var(--color-card-bg)", border: "1.5px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}
            aria-label="이전 데모"
          >
            <ArrowIcon direction="left" />
          </button>

          {/* Dots */}
          <div className="flex gap-2" role="group" aria-label="데모 슬라이드 선택">
            {demos.map((d, idx) => (
              <button
                key={d.id}
                onClick={() => goTo(idx)}
                className="w-2.5 h-2.5 rounded-full transition-all"
                style={{
                  backgroundColor: idx === activeIdx ? "var(--color-primary)" : "var(--color-border)",
                  transform: idx === activeIdx ? "scale(1.2)" : "scale(1)",
                }}
                aria-label={`${d.title} 슬라이드`}
                aria-current={idx === activeIdx ? "true" : undefined}
              />
            ))}
          </div>

          {/* Mobile next arrow */}
          <button
            onClick={goNext}
            className="demo-nav-btn sm:hidden w-9 h-9 rounded-full flex items-center justify-center"
            style={{ background: "var(--color-card-bg)", border: "1.5px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}
            aria-label="다음 데모"
          >
            <ArrowIcon direction="right" />
          </button>
        </div>
      </div>
    </section>
  );
}
