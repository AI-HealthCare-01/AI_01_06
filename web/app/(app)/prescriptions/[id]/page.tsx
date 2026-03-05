'use client';

import Link from 'next/link';
import { use } from 'react';
import Disclaimer from '@/components/common/Disclaimer';

// TODO: API 연동
const mockPrescription = {
  id: '1',
  hospital_name: '서울내과의원',
  doctor_name: '김의사',
  prescription_date: '2025-01-10',
  diagnosis: '고혈압',
  verification_status: 'CONFIRMED',
};

const mockMedications = [
  { id: '1', drug_name: '아모잘탄정 5/160mg', dosage: '1정', frequency: '1일 1회', administration: '식후 30분', duration_days: 30 },
  { id: '2', drug_name: '메트포르민정 500mg', dosage: '1정', frequency: '1일 2회', administration: '식사 중', duration_days: 30 },
  { id: '3', drug_name: '아토르바스타틴정 10mg', dosage: '1정', frequency: '1일 1회', administration: '취침 전', duration_days: 30 },
];

const mockGuide = {
  guide_markdown: '고혈압 치료를 위한 복약 안내입니다. 매일 같은 시간에 복용하시고, 임의로 중단하지 마세요.',
  precautions: '자몽 주스와 함께 복용하지 마세요. 어지러움이 심하면 즉시 의사에게 연락하세요.',
  lifestyle_advice: '저염식 식단을 유지하고, 규칙적인 유산소 운동(하루 30분)을 권장합니다.',
};

export default function PrescriptionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <div className="max-w-screen-md mx-auto px-4 py-8 flex flex-col gap-6">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <Link href="/prescriptions/list" className="text-gray-400 text-lg">← 목록</Link>
      </div>

      <div className="bg-white border-2 border-gray-200 rounded-2xl p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-extrabold text-gray-900">{mockPrescription.hospital_name}</h1>
            <p className="text-gray-500 text-lg mt-1">{mockPrescription.diagnosis} · {mockPrescription.prescription_date}</p>
            <p className="text-gray-400 text-base">담당의: {mockPrescription.doctor_name}</p>
          </div>
          <span className="bg-green-100 text-green-700 text-sm font-bold px-3 py-1 rounded-full">확정</span>
        </div>
      </div>

      {/* 약물 카드 */}
      <section>
        <h2 className="text-xl font-bold text-gray-800 mb-3">처방 약물</h2>
        <div className="flex flex-col gap-3">
          {mockMedications.map((m) => (
            <div key={m.id} className="bg-white border-2 border-gray-200 rounded-2xl p-5">
              <p className="text-xl font-bold text-gray-900 mb-2">{m.drug_name}</p>
              <div className="grid grid-cols-2 gap-2 text-base text-gray-600">
                <span>💊 용량: {m.dosage}</span>
                <span>🕐 횟수: {m.frequency}</span>
                <span>🍽️ 복용법: {m.administration}</span>
                <span>📅 기간: {m.duration_days}일</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* AI 복약 가이드 */}
      <section>
        <h2 className="text-xl font-bold text-gray-800 mb-3">AI 복약 가이드</h2>
        <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-6 flex flex-col gap-4">
          <div>
            <p className="text-base font-bold text-blue-800 mb-1">📋 복약 안내</p>
            <p className="text-gray-700 text-lg leading-relaxed">{mockGuide.guide_markdown}</p>
          </div>
          <div>
            <p className="text-base font-bold text-red-700 mb-1">⚠️ 주의사항</p>
            <p className="text-gray-700 text-lg leading-relaxed">{mockGuide.precautions}</p>
          </div>
          <div>
            <p className="text-base font-bold text-green-700 mb-1">🥗 생활습관 가이드</p>
            <p className="text-gray-700 text-lg leading-relaxed">{mockGuide.lifestyle_advice}</p>
          </div>
        </div>
        <div className="mt-3">
          <Disclaimer />
        </div>
      </section>

      {/* 액션 버튼 */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Link href={`/prescriptions/${id}/chat`}
          className="flex-1 py-4 rounded-xl text-xl font-bold text-white text-center"
          style={{ backgroundColor: '#4a90e2' }}>
          🤖 AI 상담하기
        </Link>
        <Link href={`/prescriptions/${id}/schedule`}
          className="flex-1 py-4 rounded-xl text-xl font-bold text-center border-2 border-gray-300 text-gray-700">
          📅 복약 일정 보기
        </Link>
      </div>
    </div>
  );
}
