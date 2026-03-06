"use client";

import Link from "next/link";
import AppLayout from "@/components/AppLayout";

export default function DashboardPage() {
  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-6">대시보드</h1>

      {/* Main feature cards */}
      <section className="mb-8">
        <h2 className="text-lg font-bold mb-4">주요기능</h2>
        <div className="grid grid-cols-3 gap-4">
          <Link href="/prescriptions/upload" className="bg-white rounded-lg p-6 shadow-sm text-center hover:shadow-md transition">
            <div className="w-16 h-16 bg-blue-100 rounded-lg mx-auto mb-3 flex items-center justify-center">
              <span className="text-2xl">📋</span>
            </div>
            <h3 className="font-bold">처방전 업로드</h3>
            <p className="text-sm text-gray-500 mt-1">새로운 처방전을 업로드하고 가이드를 받아보세요</p>
          </Link>
          <Link href="/guides" className="bg-white rounded-lg p-6 shadow-sm text-center hover:shadow-md transition">
            <div className="w-16 h-16 bg-green-100 rounded-lg mx-auto mb-3 flex items-center justify-center">
              <span className="text-2xl">📖</span>
            </div>
            <h3 className="font-bold">복약 가이드 확인</h3>
            <p className="text-sm text-gray-500 mt-1">이전에 생성된 가이드를 다시 확인하세요</p>
          </Link>
          <Link href="/chat" className="bg-white rounded-lg p-6 shadow-sm text-center hover:shadow-md transition">
            <div className="w-16 h-16 bg-purple-100 rounded-lg mx-auto mb-3 flex items-center justify-center">
              <span className="text-2xl">💬</span>
            </div>
            <h3 className="font-bold">AI 상담</h3>
            <p className="text-sm text-gray-500 mt-1">복약에 대해 AI에게 질문하세요</p>
          </Link>
        </div>
      </section>

      {/* Today's schedule placeholder */}
      <section className="mb-8">
        <h2 className="text-lg font-bold mb-4">오늘의 복약 일정</h2>
        <div className="bg-white rounded-lg p-6 shadow-sm text-center text-gray-400">
          아직 복약 일정이 없습니다. 처방전을 업로드하여 가이드를 생성해보세요.
        </div>
      </section>

      {/* Recent guide placeholder */}
      <section>
        <h2 className="text-lg font-bold mb-4">최근 복약 가이드</h2>
        <div className="bg-white rounded-lg p-6 shadow-sm text-center text-gray-400">
          아직 생성된 가이드가 없습니다.
        </div>
      </section>
    </AppLayout>
  );
}
