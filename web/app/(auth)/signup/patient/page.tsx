'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
import { ENDPOINTS } from '@/lib/api/endpoints';
import ErrorBox from '@/components/common/ErrorBox';

export default function PatientSignupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    name: '',
    nickname: '',
    phone_number: '',
    gender: '',
    birthdate: '',
  });

  const set = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // TODO: API 연동
      const res = await apiClient.post(ENDPOINTS.SIGNUP, { ...form, role: 'PATIENT' });
      if (res.success) {
        router.push('/profile');
      } else {
        setError(res.error?.message ?? '회원가입에 실패했습니다.');
      }
    } catch {
      setError('회원가입 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-md bg-white rounded-2xl border-2 border-gray-200 p-8 shadow-sm">
        <Link href="/signup" className="text-gray-400 text-base mb-4 block">← 뒤로</Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">환자 회원가입</h1>

        {error && <div className="mb-4"><ErrorBox message={error} /></div>}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Field label="이메일">
            <input type="email" required placeholder="example@email.com"
              value={form.email} onChange={(e) => set('email', e.target.value)}
              className={inputCls} />
          </Field>
          <Field label="비밀번호">
            <input type="password" required placeholder="8자 이상"
              value={form.password} onChange={(e) => set('password', e.target.value)}
              className={inputCls} />
          </Field>
          <Field label="비밀번호 확인">
            <input type="password" required placeholder="비밀번호를 다시 입력하세요"
              value={form.passwordConfirm} onChange={(e) => set('passwordConfirm', e.target.value)}
              className={inputCls} />
          </Field>
          <Field label="이름">
            <input type="text" required placeholder="홍길동"
              value={form.name} onChange={(e) => set('name', e.target.value)}
              className={inputCls} />
          </Field>
          <Field label="닉네임">
            <input type="text" required placeholder="보호자 연동 시 사용됩니다"
              value={form.nickname} onChange={(e) => set('nickname', e.target.value)}
              className={inputCls} />
          </Field>
          <Field label="성별">
            <div className="flex gap-3">
              {[{ v: 'M', label: '남성' }, { v: 'F', label: '여성' }].map(({ v, label }) => (
                <button key={v} type="button"
                  onClick={() => set('gender', v)}
                  className={`flex-1 py-3 rounded-xl border-2 text-lg font-semibold transition-colors ${form.gender === v ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-600'}`}>
                  {label}
                </button>
              ))}
            </div>
          </Field>
          <Field label="생년월일">
            <input type="date" required
              value={form.birthdate} onChange={(e) => set('birthdate', e.target.value)}
              className={inputCls} />
          </Field>
          <Field label="휴대폰 번호">
            <input type="tel" placeholder="010-0000-0000"
              value={form.phone_number} onChange={(e) => set('phone_number', e.target.value)}
              className={inputCls} />
          </Field>

          <button type="submit" disabled={loading}
            className="w-full py-4 rounded-xl text-xl font-bold text-white mt-2 disabled:opacity-50"
            style={{ backgroundColor: '#4a90e2' }}>
            {loading ? '처리 중...' : '다음 단계'}
          </button>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-lg font-semibold text-gray-700 mb-2">{label}</label>
      {children}
    </div>
  );
}

const inputCls = 'w-full border-2 border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:border-blue-400';
