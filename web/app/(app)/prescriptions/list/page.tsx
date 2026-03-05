'use client';

import Link from 'next/link';

// TODO: API 연동
const mockPrescriptions = [
  { id: '1', hospital_name: '서울내과의원', diagnosis: '고혈압', prescription_date: '2025-01-10', verification_status: 'CONFIRMED', medication_count: 3 },
  { id: '2', hospital_name: '한강병원', diagnosis: '당뇨', prescription_date: '2025-01-05', verification_status: 'CONFIRMED', medication_count: 2 },
  { id: '3', hospital_name: '미래의원', diagnosis: '감기', prescription_date: '2024-12-20', verification_status: 'DRAFT', medication_count: 1 },
];

const statusLabel: Record<string, { label: string; cls: string }> = {
  CONFIRMED: { label: '확정', cls: 'bg-green-100 text-green-700' },
  DRAFT: { label: '임시저장', cls: 'bg-yellow-100 text-yellow-700' },
};

export default function PrescriptionListPage() {
  return (
    <div className="max-w-screen-md mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-extrabold text-gray-900">처방전 목록</h1>
        <Link
          href="/prescriptions/upload"
          className="px-5 py-3 rounded-xl text-lg font-bold text-white"
          style={{ backgroundColor: '#4a90e2' }}
        >
          + 새 처방전
        </Link>
      </div>

      {mockPrescriptions.length === 0 ? (
        <div className="bg-white border-2 border-gray-200 rounded-2xl p-12 text-center">
          <p className="text-5xl mb-4">📋</p>
          <p className="text-xl font-semibold text-gray-700 mb-2">처방전이 없습니다</p>
          <p className="text-gray-400 text-base mb-6">처방전을 업로드하면 AI가 복약 가이드를 만들어 드립니다.</p>
          <Link href="/prescriptions/upload"
            className="inline-block px-8 py-4 rounded-xl text-lg font-bold text-white"
            style={{ backgroundColor: '#4a90e2' }}>
            처방전 업로드
          </Link>
        </div>
      ) : (
        <ul className="flex flex-col gap-4">
          {mockPrescriptions.map((p) => {
            const st = statusLabel[p.verification_status] ?? { label: p.verification_status, cls: 'bg-gray-100 text-gray-600' };
            return (
              <li key={p.id}>
                <Link href={`/prescriptions/${p.id}`}
                  className="block bg-white border-2 border-gray-200 rounded-2xl p-6 hover:border-blue-400 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-xl font-bold text-gray-900">{p.hospital_name}</span>
                        <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${st.cls}`}>{st.label}</span>
                      </div>
                      <p className="text-gray-600 text-lg">{p.diagnosis}</p>
                      <p className="text-gray-400 text-base mt-1">처방일: {p.prescription_date} · 약물 {p.medication_count}종</p>
                    </div>
                    <span className="text-gray-300 text-2xl">›</span>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
