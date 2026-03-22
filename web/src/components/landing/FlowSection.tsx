"use client";

/* ── SVG Icons ── */
function IconUpload() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM8 13h8v1.5H8V13zm0 3h8v1.5H8V16zm0-6h3v1.5H8V10z" />
    </svg>
  );
}
function IconGuide() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z" />
    </svg>
  );
}
function IconChat() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
      <path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z" />
    </svg>
  );
}

const flowSteps = [
  {
    num: "01",
    title: "처방전 업로드",
    desc: "병원에서 받은 처방전을 사진으로 찍어 올려주세요.",
    sub: "AI가 자동으로 약 이름과 용량을 인식합니다.",
    icon: <IconUpload />,
  },
  {
    num: "02",
    title: "AI 맞춤 가이드 생성",
    desc: "인식된 처방 정보를 바탕으로 복약 가이드를 만들어 드립니다.",
    sub: "복용법, 주의사항, 상호작용까지 한눈에.",
    icon: <IconGuide />,
  },
  {
    num: "03",
    title: "AI 상담으로 궁금증 해결",
    desc: "가이드를 보다 궁금한 점이 있으면 AI에게 바로 물어보세요.",
    sub: "24시간 언제든 상담 가능합니다.",
    icon: <IconChat />,
  },
];

export default function FlowSection() {
  return (
    <section
      className="py-16 px-4 sm:py-20 sm:px-6 animate-section"
      style={{ backgroundColor: "var(--color-surface)" }}
      aria-labelledby="flow-title"
    >
      <div className="max-w-3xl mx-auto">
        <h2
          id="flow-title"
          className="section-heading font-bold text-center mb-14"
          style={{ color: "var(--color-text)", fontSize: "clamp(1.25rem, 3vw, 1.75rem)" }}
        >
          이렇게 이용하세요
        </h2>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line */}
          <div
            className="absolute left-6 sm:left-8 top-0 bottom-0 w-0.5"
            style={{ background: "linear-gradient(to bottom, var(--color-primary), var(--color-secondary))" }}
            aria-hidden="true"
          />

          <div className="space-y-10 sm:space-y-12">
            {flowSteps.map((step, idx) => (
              <div key={step.num} className="relative pl-16 sm:pl-20">
                {/* Circle node */}
                <div
                  className="absolute left-3 sm:left-5 w-7 h-7 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
                  style={{
                    backgroundColor: idx === flowSteps.length - 1 ? "var(--color-secondary)" : "var(--color-primary)",
                    boxShadow: `0 0 0 4px ${idx === flowSteps.length - 1 ? "var(--color-secondary-soft)" : "var(--color-primary-soft)"}`,
                  }}
                >
                  {step.num}
                </div>

                {/* Content card */}
                <div
                  className="flow-card rounded-2xl p-5 sm:p-6"
                  style={{
                    backgroundColor: "var(--color-card-bg)",
                    border: "1.5px solid var(--color-border)",
                    boxShadow: "var(--shadow-sm)",
                  }}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span style={{ color: "var(--color-primary)" }}>{step.icon}</span>
                    <h3 className="font-bold text-lg" style={{ color: "var(--color-text)" }}>
                      {step.title}
                    </h3>
                  </div>
                  <p className="text-sm leading-relaxed mb-1" style={{ color: "var(--color-text)" }}>
                    {step.desc}
                  </p>
                  <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
                    {step.sub}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
