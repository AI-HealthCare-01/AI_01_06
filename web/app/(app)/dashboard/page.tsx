'use client';

import Link from 'next/link';

// TODO: API 연동
const mockUser = { name: '홍길동', role: 'PATIENT' as const };
const mockSchedules = [
  { id: '1', drug_name: '아모잘탄정', time_of_day: '아침', done: false },
  { id: '2', drug_name: '메트포르민정', time_of_day: '점심', done: true },
  { id: '3', drug_name: '아토르바스타틴정', time_of_day: '저녁', done: false },
];

export default function DashboardPage() {
  const today = new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });

  return (
    <div className="max-w-screen-md mx-auto px-4 py-8 flex flex-col gap-8">
      {/* 인사 */}
      <div>
        <h1 className="text-3xl font-extrabold text-gray-900">
          안녕하세요, {mockUser.name}님 👋
        </h1>
        <p className="text-gray-500 text-lg mt-1">{today}</p>
      </div>

      {/* 주요 기능 카드 */}
      <section>
        <h2 className="text-xl font-bold text-gray-700 mb-4">주요 기능</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <ActionCard href="/prescriptions/upload" emoji="📋" label="처방전 업로드" desc="처방전 사진을 찍어 등록하세요" />
          <ActionCard href="/prescriptions/list" emoji="💊" label="복약 가이드 확인" desc="내 복약 가이드를 확인하세요" />
          <ActionCard href="/chat" emoji="🤖" label="AI 상담" desc="복약 관련 궁금한 점을 물어보세요" />
        </div>
      </section>

      {/* 오늘의 복약 일정 */}
      <section>
        <h2 className="text-xl font-bold text-gray-700 mb-4">오늘의 복약 일정</h2>
        <div className="bg-white border-2 border-gray-200 rounded-2xl overflow-hidden">
          {mockSchedules.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-lg">오늘 복약 일정이 없습니다.</div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {mockSchedules.map((s) => (
                <li key={s.id} className="flex items-center justify-between px-6 py-5">
                  <div className="flex items-center gap-4">
                    <span className={`w-3 h-3 rounded-full ${s.done ? 'bg-green-400' : 'bg-gray-300'}`} />
                    <div>
                      <p className={`text-xl font-semibold ${s.done ? 'line-through text-gray-400' : 'text-gray-900'}`}>
                        {s.drug_name}
                      </p>
                      <p className="text-gray-500 text-base">{s.time_of_day}</p>
                    </div>
                  </div>
                  <span className={`text-base font-bold px-3 py-1 rounded-full ${s.done ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {s.done ? '복용 완료' : '미복용'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* 처방전 바로가기 */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-700">최근 처방전</h2>
          <Link href="/prescriptions/list" className="text-base font-semibold" style={{ color: '#4a90e2' }}>
            전체 보기
          </Link>
        </div>
        <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 text-center text-gray-400 text-lg">
          {/* TODO: API 연동 */}
          처방전을 업로드하면 여기에 표시됩니다.
        </div>
      </section>
    </div>
  );
}

function ActionCard({ href, emoji, label, desc }: { href: string; emoji: string; label: string; desc: string }) {
  return (
    <Link href={href}
      className="flex flex-col items-center gap-3 bg-white border-2 border-gray-200 rounded-2xl p-6 hover:border-blue-400 hover:bg-blue-50 transition-colors text-center">
      <span className="text-4xl">{emoji}</span>
      <span className="text-xl font-bold text-gray-900">{label}</span>
      <span className="text-gray-500 text-sm">{desc}</span>
    </Link>
  );
}
