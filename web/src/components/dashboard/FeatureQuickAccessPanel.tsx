import Link from "next/link";

interface Props {
  loading: boolean;
}

export default function FeatureQuickAccessPanel({ loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[0, 1, 2].map((i) => (
          <div key={i} className="app-card rounded-lg p-6 animate-pulse">
            <div
              className="w-16 h-16 rounded-2xl mx-auto mb-3"
              style={{ background: "var(--color-border)" }}
            />
            <div
              className="h-4 rounded mx-auto w-3/4 mb-2"
              style={{ background: "var(--color-border)" }}
            />
            <div
              className="h-3 rounded mx-auto w-full"
              style={{ background: "var(--color-border)" }}
            />
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="mb-8">
      <h2 className="text-lg font-bold mb-4">주요기능</h2>
      <div className="grid grid-cols-3 gap-4">
        <Link href="/prescriptions/upload" className="app-card rounded-lg p-6 text-center">
          <div
            className="w-16 h-16 rounded-2xl mx-auto mb-3 flex items-center justify-center"
            style={{ background: "var(--color-primary-soft)" }}
          >
            <svg width="40" height="40" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="6" y="4" width="20" height="24" rx="3" stroke="var(--color-primary)" strokeWidth="2" fill="none" />
              <path d="M12 4V2a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" />
              <line x1="11" y1="13" x2="21" y2="13" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
              <line x1="11" y1="17" x2="21" y2="17" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
              <line x1="11" y1="21" x2="17" y2="21" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
              <circle cx="22" cy="22" r="6" fill="var(--color-primary)" />
              <path d="M22 19v6M19 22h6" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <h3 className="font-bold">처방전 업로드</h3>
          <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
            새로운 처방전을 업로드하고 가이드를 받아보세요
          </p>
        </Link>
        <Link href="/guides" className="app-card rounded-lg p-6 text-center">
          <div
            className="w-16 h-16 rounded-2xl mx-auto mb-3 flex items-center justify-center"
            style={{ background: "var(--color-success-soft)" }}
          >
            <svg width="40" height="40" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 6a3 3 0 0 1 3-3h6l1 1v22l-1 1H9a3 3 0 0 1-3-3V6Z" stroke="var(--color-primary)" strokeWidth="2" fill="none" />
              <path d="M26 6a3 3 0 0 0-3-3h-6l-1 1v22l1 1h6a3 3 0 0 0 3-3V6Z" stroke="var(--color-primary)" strokeWidth="2" fill="none" />
              <path d="M16 5v22" stroke="var(--color-primary)" strokeWidth="1.5" opacity="0.3" />
              <circle cx="11" cy="11" r="1.5" fill="var(--color-primary)" opacity="0.5" />
              <line x1="9" y1="15" x2="14" y2="15" stroke="var(--color-primary)" strokeWidth="1.2" strokeLinecap="round" opacity="0.4" />
              <line x1="9" y1="18" x2="13" y2="18" stroke="var(--color-primary)" strokeWidth="1.2" strokeLinecap="round" opacity="0.4" />
              <path d="M20 10l1.5 1.5L25 8" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M20 15l1.5 1.5L25 13" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.5" />
            </svg>
          </div>
          <h3 className="font-bold">복약 가이드 확인</h3>
          <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
            이전에 생성된 가이드를 다시 확인하세요
          </p>
        </Link>
        <Link href="/chat" className="app-card rounded-lg p-6 text-center">
          <div
            className="w-16 h-16 rounded-2xl mx-auto mb-3 flex items-center justify-center"
            style={{ background: "rgba(232, 129, 90, 0.15)" }}
          >
            <svg width="40" height="40" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="5" width="24" height="17" rx="4" stroke="var(--color-accent)" strokeWidth="2" fill="none" />
              <path d="M12 26l-3 3v-3" stroke="var(--color-accent)" strokeWidth="2" strokeLinejoin="round" fill="none" />
              <circle cx="11" cy="13.5" r="1.5" fill="var(--color-accent)" opacity="0.6" />
              <circle cx="16" cy="13.5" r="1.5" fill="var(--color-accent)" opacity="0.6" />
              <circle cx="21" cy="13.5" r="1.5" fill="var(--color-accent)" opacity="0.6" />
              <circle cx="25" cy="8" r="5" fill="var(--color-accent)" />
              <path d="M23.5 8h3M25 6.5v3" stroke="#fff" strokeWidth="1.3" strokeLinecap="round" />
            </svg>
          </div>
          <h3 className="font-bold">AI 상담</h3>
          <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
            복약에 대해 AI에게 질문하세요
          </p>
        </Link>
      </div>
    </section>
  );
}
