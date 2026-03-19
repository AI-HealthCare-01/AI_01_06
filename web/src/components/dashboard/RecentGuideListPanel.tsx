"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, GuideItem } from "@/lib/api";

export default function RecentGuideListPanel() {
  const [guides, setGuides] = useState<GuideItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listGuides().then((res) => {
      if (res.success && res.data) setGuides(res.data.slice(0, 3));
      setLoading(false);
    });
  }, []);

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold" style={{ color: "var(--color-text)" }}>최근 복약 가이드</h2>
        {guides.length > 0 && (
          <Link
            href="/guides"
            className="text-sm font-medium hover:underline"
            style={{ color: "var(--color-primary)" }}
          >
            전체보기 →
          </Link>
        )}
      </div>

      {loading ? (
        <div className="app-card p-8 text-center" style={{ color: "var(--color-text-muted)" }}>
          로딩 중...
        </div>
      ) : guides.length === 0 ? (
        <div className="app-card p-8 text-center">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="var(--color-border)" className="mx-auto mb-3">
            <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM8 13h8v1.5H8V13zm0 3h8v1.5H8V16z"/>
          </svg>
          <p className="text-base" style={{ color: "var(--color-text-muted)" }}>
            아직 생성된 가이드가 없습니다
          </p>
          <Link
            href="/prescriptions/upload"
            className="inline-block mt-4 px-6 py-2.5 rounded-xl text-sm font-semibold btn-primary"
          >
            처방전 업로드하기
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {guides.map((guide) => (
            <Link key={guide.id} href={`/guides/${guide.id}`} className="block app-card p-5">
              <div className="flex items-center gap-4">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: "var(--color-primary-soft)" }}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--color-primary)">
                    <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z"/>
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-base font-bold truncate" style={{ color: "var(--color-text)" }}>
                    {guide.prescription_info.hospital_name || "병원명 미입력"}
                  </p>
                  <div className="flex gap-3 text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
                    <span>{guide.prescription_info.diagnosis || "-"}</span>
                    <span>{guide.prescription_info.prescription_date || "-"}</span>
                  </div>
                </div>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--color-text-muted)" className="flex-shrink-0">
                  <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                </svg>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
