import Link from 'next/link';

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8 text-center">{children}</h2>;
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
      <div className="text-xl font-bold text-gray-900 mb-2">{title}</div>
      <div className="text-gray-600 text-lg">{desc}</div>
    </div>
  );
}

function ListItem({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-gray-100 rounded-xl px-6 py-5 text-gray-800 text-xl font-medium">
      {children}
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">

      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-screen-xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-2xl font-extrabold tracking-tight text-indigo-700">SULLIVAN</span>
          <nav className="flex items-center gap-3">
            <button
              className="hidden sm:inline-flex text-sm text-gray-500 border border-gray-300 rounded-lg px-3 py-1.5 hover:bg-gray-50"
              aria-label="글씨 크기 조절"
            >
              가 / 가
            </button>
            <Link
              href="/login"
              className="text-lg font-semibold text-gray-700 border border-gray-300 rounded-xl px-5 py-2 hover:bg-gray-50"
            >
              로그인
            </Link>
            <Link
              href="/signup"
              className="text-lg font-semibold text-white bg-indigo-600 rounded-xl px-5 py-2 hover:bg-indigo-700"
            >
              회원가입
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-6">

        {/* Hero / 소개 이미지 */}
        <section className="py-16 flex flex-col items-center">
          <div className="bg-gray-200 rounded-3xl w-full h-64 md:h-96 flex items-center justify-center">
            <span className="text-gray-500 text-2xl font-medium">소개 이미지</span>
          </div>
        </section>

        {/* 이용방법 */}
        <section className="py-16 flex flex-col items-center">
          <SectionTitle>이용방법</SectionTitle>
          <div className="flex flex-col items-center gap-0 max-w-lg mx-auto">
            {[
              { num: '1', label: '처방전 업로드' },
              { num: '2', label: 'AI 가이드 생성' },
              { num: '3', label: 'AI 상담' },
            ].map((step, i, arr) => (
              <div key={step.num} className="flex flex-col items-center w-full">
                <div className="w-full bg-white border border-gray-200 rounded-2xl px-8 py-6 flex items-center gap-5 shadow-sm">
                  <span className="text-3xl font-extrabold text-indigo-600 w-10 shrink-0">{step.num}</span>
                  <span className="text-2xl font-semibold text-gray-900">{step.label}</span>
                </div>
                {i < arr.length - 1 && (
                  <div className="text-gray-400 text-3xl my-2" aria-hidden="true">↓</div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* 기능 안내 */}
        <section className="py-16 flex flex-col items-center">
          <SectionTitle>기능 안내</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
            <FeatureCard title="환자 대시보드" desc="복약 현황과 일정을 한눈에 확인하세요." />
            <FeatureCard title="보호자 모드" desc="가족의 복약 상태를 원격으로 관리하세요." />
            <FeatureCard title="복약 알림" desc="정해진 시간에 알림을 받아 복약을 놓치지 마세요." />
            <FeatureCard title="안전한 보안" desc="개인 의료 정보를 안전하게 보호합니다." />
          </div>
        </section>

        {/* 대상 안내 */}
        <section className="py-16 flex flex-col items-center">
          <SectionTitle>이런 분께 도움이 됩니다</SectionTitle>
          <div className="flex flex-col gap-4 w-full max-w-2xl">
            <ListItem>여러 가지 약을 복용하시는 어르신</ListItem>
            <ListItem>부모님의 약 관리가 걱정되시는 보호자</ListItem>
            <ListItem>약 복용 시간과 방법이 헷갈리시는 분</ListItem>
            <ListItem>병원 진료 시간이 짧아 자세히 못 여쭤보신 분</ListItem>
          </div>
        </section>

        {/* 하단 CTA */}
        <section className="py-20 text-center">
          <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-8">지금 바로 시작하세요</h2>
          <Link
            href="/signup"
            className="inline-block text-2xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-2xl px-14 py-6"
          >
            무료로 회원가입
          </Link>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-8">
        <div className="max-w-screen-xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-3 gap-10">
          <div>
            <div className="text-xl font-extrabold text-indigo-700 mb-2">SULLIVAN</div>
            <p className="text-gray-500 text-base">AI 기반 복약 관리 서비스</p>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-800 mb-3">고객지원</div>
            <p className="text-gray-600 text-base mb-1">📞 010-0000-0000</p>
            <p className="text-gray-600 text-base">✉ support@sullivan.example.com</p>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-800 mb-3">법적 고지</div>
            <div className="flex flex-col gap-2">
              <Link href="/legal/privacy" className="text-gray-600 text-base hover:underline">개인정보처리방침</Link>
              <Link href="/legal/terms" className="text-gray-600 text-base hover:underline">이용약관</Link>
            </div>
          </div>
        </div>
        <div className="text-center text-gray-400 text-sm pb-6">© 2025 Sullivan. All rights reserved.</div>
      </footer>

    </div>
  );
}
