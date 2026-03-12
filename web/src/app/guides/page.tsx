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

export default function GuidesListPage() {
  const [guides, setGuides] = useState<GuideItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listGuides().then((res) => {
      if (res.success && res.data) setGuides(res.data as GuideItem[]);
      setLoading(false);
    });
  }, []);

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">가이드 기록</h1>
          <p style={{ color: 'var(--color-text-muted)' }}>이전에 생성된 복약 가이드를 확인하세요</p>
        </div>
        <Link href="/prescriptions/upload" className="px-4 py-2 rounded-lg btn-primary">
          가이드 생성
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="app-card rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{guides.length}</p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>총 가이드 수</p>
        </div>
        <div className="app-card rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">-</p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>복용 중</p>
        </div>
        <div className="app-card rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{guides.length}</p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>완료됨</p>
        </div>
      </div>

      {loading ? (
        <p className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>로딩 중...</p>
      ) : guides.length === 0 ? (
        <p className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>아직 생성된 가이드가 없습니다.</p>
      ) : (
        <div className="space-y-4">
          {guides.map((guide) => (
            <div key={guide.id} className="app-card rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold">{guide.prescription_info.hospital_name || "병원명 미입력"}</h3>
                  <div className="flex gap-4 text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                    <span>처방일 {guide.prescription_info.prescription_date}</span>
                    <span>담당의 {guide.prescription_info.doctor_name}</span>
                    <span>진단 {guide.prescription_info.diagnosis}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link href={`/guides/${guide.id}`} className="text-sm px-3 py-1 rounded btn-outline">
                    가이드 보기
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
