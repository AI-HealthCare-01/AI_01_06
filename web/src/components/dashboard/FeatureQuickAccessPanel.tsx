import Link from "next/link";

interface Props {
  loading: boolean;
}

function IconPrescription() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
      <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM8 13h8v1.5H8V13zm0 3h8v1.5H8V16zm0-6h3v1.5H8V10z"/>
    </svg>
  );
}

function IconGuide() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z"/>
    </svg>
  );
}

function IconChat() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      <path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/>
    </svg>
  );
}

export default function FeatureQuickAccessPanel({ loading }: Props) {
  if (loading) {
    return (
      <section className="mb-8">
        <div
          className="h-5 rounded w-24 mb-4"
          style={{ background: "var(--color-surface-alt)" }}
        />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="app-card p-6 animate-pulse">
              <div
                className="w-14 h-14 rounded-2xl mb-4"
                style={{ background: "var(--color-surface-alt)" }}
              />
              <div
                className="h-5 rounded w-3/4 mb-2"
                style={{ background: "var(--color-surface-alt)" }}
              />
              <div
                className="h-4 rounded w-full"
                style={{ background: "var(--color-surface-alt)" }}
              />
            </div>
          ))}
        </div>
      </section>
    );
  }

  const features = [
    {
      href: "/prescriptions/upload",
      icon: <IconPrescription />,
      iconBg: "var(--color-primary-soft)",
      iconColor: "var(--color-primary)",
      title: "처방전 업로드",
      description: "새로운 처방전을 업로드하고 가이드를 받아보세요",
    },
    {
      href: "/guides",
      icon: <IconGuide />,
      iconBg: "var(--color-success-soft)",
      iconColor: "var(--color-success)",
      title: "복약 가이드 확인",
      description: "이전에 생성된 가이드를 다시 확인하세요",
    },
    {
      href: "/chat",
      icon: <IconChat />,
      iconBg: "var(--color-secondary-soft)",
      iconColor: "var(--color-secondary)",
      title: "AI 상담",
      description: "복약에 대해 AI에게 질문하세요",
    },
  ];

  return (
    <section className="mb-8">
      <h2 className="text-xl font-bold mb-4" style={{ color: "var(--color-text)" }}>주요기능</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {features.map((f) => (
          <Link key={f.href} href={f.href} className="app-card p-6 flex md:flex-col items-center md:items-start gap-4">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
              style={{ background: f.iconBg, color: f.iconColor }}
            >
              {f.icon}
            </div>
            <div>
              <h3 className="text-base font-bold" style={{ color: "var(--color-text)" }}>{f.title}</h3>
              <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
                {f.description}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
