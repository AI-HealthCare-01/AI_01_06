"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface PrescriptionItem {
  id: number;
  hospital_name: string;
  doctor_name: string;
  prescription_date: string;
  diagnosis: string;
  medication_count: number;
}

export default function GuidesListPage() {
  const [prescriptions, setPrescriptions] = useState<PrescriptionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listPrescriptions().then((res) => {
      if (res.success && res.data) setPrescriptions(res.data as PrescriptionItem[]);
      setLoading(false);
    });
  }, []);

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">가이드 기록</h1>
          <p className="text-gray-600">이전에 생성된 복약 가이드를 확인하세요</p>
        </div>
        <Link href="/prescriptions/upload" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          가이드 생성
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg p-4 text-center shadow-sm">
          <p className="text-2xl font-bold">{prescriptions.length}</p>
          <p className="text-sm text-gray-500">총 가이드 수</p>
        </div>
        <div className="bg-white rounded-lg p-4 text-center shadow-sm">
          <p className="text-2xl font-bold">-</p>
          <p className="text-sm text-gray-500">복용 중</p>
        </div>
        <div className="bg-white rounded-lg p-4 text-center shadow-sm">
          <p className="text-2xl font-bold">-</p>
          <p className="text-sm text-gray-500">완료됨</p>
        </div>
      </div>

      {loading ? (
        <p className="text-gray-500 text-center py-8">로딩 중...</p>
      ) : prescriptions.length === 0 ? (
        <p className="text-gray-400 text-center py-8">아직 생성된 가이드가 없습니다.</p>
      ) : (
        <div className="space-y-4">
          {prescriptions.map((p) => (
            <div key={p.id} className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold">{p.hospital_name || "병원명 미입력"}</h3>
                  <div className="flex gap-4 text-sm text-gray-500 mt-1">
                    <span>처방일 {p.prescription_date}</span>
                    <span>담당의 {p.doctor_name}</span>
                    <span>진단 {p.diagnosis}</span>
                    <span>처방 약물 {p.medication_count}개</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link href={`/prescriptions/${p.id}/ocr`} className="text-sm border px-3 py-1 rounded hover:bg-gray-50">
                    상세보기
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
