"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface GuideItem {
  id: number;
  prescription_id: number;
  status: string;
  prescription_info: {
    hospital_name: string;
    doctor_name: string;
    prescription_date: string;
    diagnosis: string;
  };
  created_at: string;
}

export default function DashboardPage() {
  const [guides, setGuides] = useState<GuideItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listGuides().then((res) => {
      if (res.success && res.data) setGuides(res.data as GuideItem[]);
      setLoading(false);
    });
  }, []);

  const recentGuides = guides.slice(0, 3);

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

      {/* Recent guides */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">최근 복약 가이드</h2>
          {guides.length > 0 && (
            <Link href="/guides" className="text-sm text-blue-600 hover:underline">전체보기</Link>
          )}
        </div>

        {loading ? (
          <div className="bg-white rounded-lg p-6 shadow-sm text-center text-gray-400">로딩 중...</div>
        ) : recentGuides.length === 0 ? (
          <div className="bg-white rounded-lg p-6 shadow-sm text-center text-gray-400">
            아직 생성된 가이드가 없습니다.
          </div>
        ) : (
          <div className="space-y-3">
            {recentGuides.map((guide) => (
              <Link key={guide.id} href={`/guides/${guide.id}`} className="block bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-bold">{guide.prescription_info.hospital_name || "병원명 미입력"}</p>
                    <div className="flex gap-3 text-sm text-gray-500 mt-1">
                      <span>진단: {guide.prescription_info.diagnosis || "-"}</span>
                      <span>처방일: {guide.prescription_info.prescription_date || "-"}</span>
                    </div>
                  </div>
                  <span className="text-sm text-blue-600">가이드 보기 →</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </AppLayout>
  );
}
