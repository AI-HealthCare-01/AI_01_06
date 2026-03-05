'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { removeToken } from '@/lib/auth/token';

// TODO: API 연동
const mockUser = { name: '홍길동', email: 'hong@example.com', role: 'PATIENT', nickname: '길동이', phone_number: '010-****-5678' };
const mockProfile = { height_cm: 170, weight_kg: 68, has_allergies: true, allergy_details: '페니실린', has_diseases: true, disease_details: '고혈압' };

export default function MyPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'info' | 'health' | 'settings'>('info');

  const handleLogout = () => {
    removeToken();
    router.push('/login');
  };

  return (
    <div className="max-w-screen-md mx-auto px-4 py-8">
      {/* 프로필 헤더 */}
      <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 flex items-center gap-5 mb-6">
        <div className="w-20 h-20 rounded-full flex items-center justify-center text-4xl"
          style={{ backgroundColor: '#e8f0fb' }}>
          {mockUser.role === 'PATIENT' ? '🧑⚕️' : '👨👩👧'}
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">{mockUser.name}</h1>
          <p className="text-gray-500 text-lg">{mockUser.role === 'PATIENT' ? '환자' : '보호자'}</p>
          <p className="text-gray-400 text-base">{mockUser.email}</p>
        </div>
      </div>

      {/* 탭 */}
      <div className="flex border-b-2 border-gray-200 mb-6">
        {([['info', '기본 정보'], ['health', '건강 정보'], ['settings', '설정']] as const).map(([tab, label]) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 text-lg font-semibold border-b-2 -mb-0.5 transition-colors ${activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* 기본 정보 탭 */}
      {activeTab === 'info' && (
        <div className="flex flex-col gap-4">
          <InfoRow label="이름" value={mockUser.name} />
          <InfoRow label="닉네임" value={mockUser.nickname} />
          <InfoRow label="이메일" value={mockUser.email} />
          <InfoRow label="휴대폰" value={mockUser.phone_number} />
          <button className="w-full py-4 rounded-xl border-2 border-gray-300 text-lg font-semibold text-gray-700 mt-2">
            정보 수정
          </button>
        </div>
      )}

      {/* 건강 정보 탭 */}
      {activeTab === 'health' && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white border-2 border-gray-200 rounded-2xl p-5 text-center">
              <p className="text-gray-500 text-base mb-1">키</p>
              <p className="text-3xl font-extrabold text-gray-900">{mockProfile.height_cm}<span className="text-lg font-normal text-gray-500">cm</span></p>
            </div>
            <div className="bg-white border-2 border-gray-200 rounded-2xl p-5 text-center">
              <p className="text-gray-500 text-base mb-1">몸무게</p>
              <p className="text-3xl font-extrabold text-gray-900">{mockProfile.weight_kg}<span className="text-lg font-normal text-gray-500">kg</span></p>
            </div>
          </div>
          <InfoRow label="알레르기" value={mockProfile.has_allergies ? mockProfile.allergy_details ?? '있음' : '없음'} />
          <InfoRow label="기저질환" value={mockProfile.has_diseases ? mockProfile.disease_details ?? '있음' : '없음'} />
          <button className="w-full py-4 rounded-xl border-2 border-gray-300 text-lg font-semibold text-gray-700 mt-2">
            건강 정보 수정
          </button>
        </div>
      )}

      {/* 설정 탭 */}
      {activeTab === 'settings' && (
        <div className="flex flex-col gap-3">
          <SettingItem label="알림 설정" emoji="🔔" />
          <SettingItem label="글씨 크기 설정" emoji="🔤" />
          <SettingItem label="개인정보처리방침" emoji="📄" />
          <SettingItem label="이용약관" emoji="📋" />
          <button
            onClick={handleLogout}
            className="w-full py-4 rounded-xl border-2 border-red-200 text-red-500 text-lg font-semibold mt-4">
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border-2 border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between">
      <span className="text-gray-500 text-lg">{label}</span>
      <span className="text-gray-900 text-lg font-semibold">{value}</span>
    </div>
  );
}

function SettingItem({ label, emoji }: { label: string; emoji: string }) {
  return (
    <button className="w-full bg-white border-2 border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between hover:border-blue-300 transition-colors">
      <span className="flex items-center gap-3 text-lg font-semibold text-gray-800">
        <span>{emoji}</span>{label}
      </span>
      <span className="text-gray-300 text-xl">›</span>
    </button>
  );
}
