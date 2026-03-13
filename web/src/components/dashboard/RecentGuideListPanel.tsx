"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface GuideItem {
  id: number;
  prescription_info: {
    hospital_name: string;
    diagnosis: string;
    prescription_date: string;
  };
}

export default function RecentGuideListPanel() {
  const [guides, setGuides] = useState<GuideItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listGuides().then((res) => {
      if (res.success && res.data) setGuides((res.data as GuideItem[]).slice(0, 3));
      setLoading(false);
    });
  }, []);

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold">최근 복약 가이드</h2>
        {guides.length > 0 && (
          <Link
            href="/guides"
            className="text-sm hover:underline"
            style={{ color: "var(--color-primary)" }}
          >
            전체보기
          </Link>
        )}
      </div>

      {loading ? (
        <div
          className="app-card rounded-lg p-6 text-center"
          style={{ color: "var(--color-text-muted)" }}
        >
          로딩 중...
        </div>
      ) : guides.length === 0 ? (
        <div
          className="app-card rounded-lg p-6 text-center"
          style={{ color: "var(--color-text-muted)" }}
        >
          아직 생성된 가이드가 없습니다.
        </div>
      ) : (
        <div className="space-y-3">
          {guides.map((guide) => (
            <Link key={guide.id} href={`/guides/${guide.id}`} className="block app-card rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-bold">
                    {guide.prescription_info.hospital_name || "병원명 미입력"}
                  </p>
                  <div
                    className="flex gap-3 text-sm mt-1"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    <span>진단: {guide.prescription_info.diagnosis || "-"}</span>
                    <span>처방일: {guide.prescription_info.prescription_date || "-"}</span>
                  </div>
                </div>
                <span className="text-sm" style={{ color: "var(--color-primary)" }}>
                  가이드 보기 →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
