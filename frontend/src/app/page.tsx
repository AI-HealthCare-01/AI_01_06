"use client";

import Link from "next/link";
import Header from "@/components/Header";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Header />

      {/* Hero */}
      <section className="bg-gradient-to-b from-blue-50 to-white py-20 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          AI 맞춤형 복약 가이드
        </h1>
        <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
          처방전을 업로드하면 AI가 맞춤형 복약 지침과 건강 관리 가이드를 제공합니다.
        </p>
        <Link
          href="/signup"
          className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700"
        >
          지금 바로 시작하세요
        </Link>
      </section>

      {/* How it works */}
      <section className="py-16 px-6 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-center mb-10">이용방법</h2>
        <div className="space-y-4">
          {["처방전 업로드", "AI 가이드 생성", "AI 상담"].map((step, i) => (
            <div key={step} className="bg-gray-100 rounded-lg p-4 text-center">
              <span className="text-gray-500 text-sm">Step {i + 1}</span>
              <p className="font-medium text-lg">{step}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-6 bg-gray-50">
        <h2 className="text-2xl font-bold text-center mb-10">기능 안내</h2>
        <div className="max-w-4xl mx-auto grid grid-cols-2 gap-6">
          {[
            { title: "환자 대시보드", desc: "복약 일정과 가이드를 한눈에 확인" },
            { title: "보호자 모드", desc: "가족의 복약 현황을 함께 관리" },
            { title: "복약 알림", desc: "시간에 맞춰 복약 알림 제공" },
            { title: "안전한 보안", desc: "개인 정보를 안전하게 보호" },
          ].map((f) => (
            <div key={f.title} className="bg-white rounded-lg p-8 text-center shadow-sm">
              <h3 className="font-bold text-lg mb-2">{f.title}</h3>
              <p className="text-gray-600 text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Target users */}
      <section className="py-16 px-6 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-center mb-10">이런분께 도움이 됩니다</h2>
        <div className="space-y-3">
          {[
            "여러 가지 약을 복용하시는 어르신",
            "부모님의 약 관리가 걱정되시는 보호자",
            "약 복용 시간과 방법이 헷갈리시는 분",
            "병원 진료 시간이 짧아 자세히 못 여쭤보신 분",
          ].map((t) => (
            <div key={t} className="bg-blue-50 rounded-lg p-4 text-center text-blue-800">
              {t}
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-100 py-8 px-6">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between gap-6">
          <div>
            <p className="font-bold text-lg mb-2">& Sullivan</p>
          </div>
          <div>
            <p className="font-bold mb-1">고객지원</p>
            <p className="text-sm text-gray-600">전화: 000-000-0000</p>
            <p className="text-sm text-gray-600">이메일: support@sullivan.com</p>
          </div>
          <div>
            <p className="font-bold mb-1">법적 고지 안내</p>
            <p className="text-sm text-gray-600 hover:underline cursor-pointer">개인정보처리안내</p>
            <p className="text-sm text-gray-600 hover:underline cursor-pointer">이용안내</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
