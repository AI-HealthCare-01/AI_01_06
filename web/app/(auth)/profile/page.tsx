'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
import { ENDPOINTS } from '@/lib/api/endpoints';
import ErrorBox from '@/components/common/ErrorBox';

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    height_cm: '',
    weight_kg: '',
    has_allergies: false,
    allergy_details: '',
    has_diseases: false,
    disease_details: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // TODO: API 연동
      const res = await apiClient.post(ENDPOINTS.PATIENT_PROFILE, {
        height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
        has_allergies: form.has_allergies,
        allergy_details: form.allergy_details || null,
        has_diseases: form.has_diseases,
        disease_details: form.disease_details || null,
      });
      if (res.success) {
        router.push('/dashboard');
      } else {
        setError(res.error?.message ?? '저장에 실패했습니다.');
      }
    } catch {
      setError('저장 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-md bg-white rounded-2xl border-2 border-gray-200 p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">건강 정보 입력</h1>
        <p className="text-gray-500 text-base mb-6">맞춤형 복약 가이드를 위해 건강 정보를 입력해 주세요.</p>

        {error && <div className="mb-4"><ErrorBox message={error} /></div>}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-lg font-semibold text-gray-700 mb-2">키 (cm)</label>
              <input type="number" placeholder="예: 165"
                value={form.height_cm} onChange={(e) => setForm((f) => ({ ...f, height_cm: e.target.value }))}
                className={inputCls} />
            </div>
            <div className="flex-1">
              <label className="block text-lg font-semibold text-gray-700 mb-2">몸무게 (kg)</label>
              <input type="number" placeholder="예: 60"
                value={form.weight_kg} onChange={(e) => setForm((f) => ({ ...f, weight_kg: e.target.value }))}
                className={inputCls} />
            </div>
          </div>

          <ToggleField
            label="알레르기가 있으신가요?"
            value={form.has_allergies}
            onChange={(v) => setForm((f) => ({ ...f, has_allergies: v }))}
          />
          {form.has_allergies && (
            <div>
              <label className="block text-base font-semibold text-gray-700 mb-2">알레르기 상세 내용</label>
              <textarea placeholder="예: 페니실린, 아스피린 등"
                value={form.allergy_details}
                onChange={(e) => setForm((f) => ({ ...f, allergy_details: e.target.value }))}
                rows={3}
                className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:border-blue-400 resize-none" />
            </div>
          )}

          <ToggleField
            label="기저질환이 있으신가요?"
            value={form.has_diseases}
            onChange={(v) => setForm((f) => ({ ...f, has_diseases: v }))}
          />
          {form.has_diseases && (
            <div>
              <label className="block text-base font-semibold text-gray-700 mb-2">기저질환 상세 내용</label>
              <textarea placeholder="예: 고혈압, 당뇨 등"
                value={form.disease_details}
                onChange={(e) => setForm((f) => ({ ...f, disease_details: e.target.value }))}
                rows={3}
                className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:border-blue-400 resize-none" />
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full py-4 rounded-xl text-xl font-bold text-white mt-2 disabled:opacity-50"
            style={{ backgroundColor: '#4a90e2' }}>
            {loading ? '저장 중...' : '저장하고 시작하기'}
          </button>

          <button type="button" onClick={() => router.push('/dashboard')}
            className="w-full py-3 rounded-xl text-lg font-semibold text-gray-500 border-2 border-gray-200">
            나중에 입력하기
          </button>
        </form>
      </div>
    </div>
  );
}

function ToggleField({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between border-2 border-gray-200 rounded-xl px-4 py-4">
      <span className="text-lg font-semibold text-gray-700">{label}</span>
      <div className="flex gap-2">
        {[{ v: true, label: '예' }, { v: false, label: '아니오' }].map(({ v, label: l }) => (
          <button key={String(v)} type="button" onClick={() => onChange(v)}
            className={`px-4 py-2 rounded-lg text-base font-semibold border-2 transition-colors ${value === v ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-500'}`}>
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}

const inputCls = 'w-full border-2 border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:border-blue-400';
