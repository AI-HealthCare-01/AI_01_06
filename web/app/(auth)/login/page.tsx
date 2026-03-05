'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuth } from '@/lib/hooks/useAuth';
import ErrorBox from '@/components/common/ErrorBox';

export default function LoginPage() {
  const { login, loading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, password);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl border-2 border-gray-200 p-8 shadow-sm">
        <Link href="/" className="block text-center text-3xl font-extrabold mb-8" style={{ color: '#4a90e2' }}>
          설리반
        </Link>

        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">로그인</h1>

        {error && <div className="mb-4"><ErrorBox message={error} /></div>}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-lg font-semibold text-gray-700 mb-2">이메일</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="이메일을 입력하세요"
              required
              className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:border-blue-400"
            />
          </div>
          <div>
            <label className="block text-lg font-semibold text-gray-700 mb-2">비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요"
              required
              className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:border-blue-400"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-xl text-xl font-bold text-white mt-2 disabled:opacity-50"
            style={{ backgroundColor: '#4a90e2' }}
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        {/* 소셜 로그인 */}
        <div className="mt-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-gray-400 text-sm">또는</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>
          <div className="flex flex-col gap-3">
            <button
              onClick={() => { /* TODO: API 연동 - 카카오 OAuth */ }}
              className="w-full py-4 rounded-xl text-lg font-bold border-2 border-yellow-400 bg-yellow-400 text-gray-900"
            >
              카카오로 로그인
            </button>
            <button
              onClick={() => { /* TODO: API 연동 - 구글 OAuth */ }}
              className="w-full py-4 rounded-xl text-lg font-bold border-2 border-gray-300 bg-white text-gray-700"
            >
              구글로 로그인
            </button>
          </div>
        </div>

        <div className="mt-6 text-center text-lg text-gray-500">
          계정이 없으신가요?{' '}
          <Link href="/signup" className="font-bold" style={{ color: '#4a90e2' }}>
            회원가입
          </Link>
        </div>
      </div>
    </div>
  );
}
