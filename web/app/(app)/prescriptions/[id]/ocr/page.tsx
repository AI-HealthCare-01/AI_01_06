'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import ParsedFieldsForm from '@/components/ocr/ParsedFieldsForm';
import type { Medication } from '@/lib/api/types';
import { apiClient } from '@/lib/api/client';
import { ENDPOINTS } from '@/lib/api/endpoints';
import ErrorBox from '@/components/common/ErrorBox';

// TODO: API 연동 - OCR 결과 불러오기
const mockMedications: Partial<Medication>[] = [
  { drug_name: '아모잘탄정 5/160mg', dosage: '1정', frequency: '1일 1회', administration: '식후 30분', duration_days: 30 },
  { drug_name: '메트포르민정 500mg', dosage: '1정', frequency: '1일 2회', administration: '식사 중', duration_days: 30 },
];

export default function OcrReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [medications, setMedications] = useState<Partial<Medication>[]>(mockMedications);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (index: number, field: keyof Medication, value: string) => {
    setMedications((prev) => prev.map((m, i) => i === index ? { ...m, [field]: value } : m));
  };

  const handleRemove = (index: number) => {
    setMedications((prev) => prev.filter((_, i) => i !== index));
  };

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    try {
      // TODO: API 연동 - 처방전 확정
      const res = await apiClient.post(ENDPOINTS.PRESCRIPTION_CONFIRM(id), { medications });
      if (res.success) {
        router.push(`/prescriptions/${id}`);
      } else {
        setError(res.error?.message ?? '확정에 실패했습니다.');
      }
    } catch {
      setError('처리 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-screen-md mx-auto px-4 py-8">
      <h1 className="text-3xl font-extrabold text-gray-900 mb-2">OCR 결과 확인</h1>
      <p className="text-gray-500 text-lg mb-6">AI가 인식한 약물 정보를 확인하고 수정해 주세요.</p>

      {error && <div className="mb-4"><ErrorBox message={error} /></div>}

      <ParsedFieldsForm medications={medications} onChange={handleChange} onRemove={handleRemove} />

      <button
        onClick={() => setMedications((prev) => [...prev, { drug_name: '', dosage: '', frequency: '', administration: '', duration_days: 0 }])}
        className="w-full mt-4 py-4 rounded-xl border-2 border-dashed border-gray-300 text-lg font-semibold text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-colors"
      >
        + 약물 추가
      </button>

      <button
        onClick={handleConfirm}
        disabled={loading || medications.length === 0}
        className="w-full mt-6 py-5 rounded-xl text-xl font-bold text-white disabled:opacity-40"
        style={{ backgroundColor: '#4a90e2' }}
      >
        {loading ? 'AI 가이드 생성 중...' : '확정하고 복약 가이드 받기'}
      </button>
    </div>
  );
}
