"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { usePatient } from "@/lib/patient-context";

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

type SortKey = "date_desc" | "date_asc" | "name_asc" | "name_desc";

function sortGuides(guides: GuideItem[], sort: SortKey): GuideItem[] {
  return [...guides].sort((a, b) => {
    const nameA = a.prescription_info.hospital_name || "";
    const nameB = b.prescription_info.hospital_name || "";
    if (sort === "date_desc") return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    if (sort === "date_asc") return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    if (sort === "name_asc") return nameA.localeCompare(nameB, "ko");
    if (sort === "name_desc") return nameB.localeCompare(nameA, "ko");
    return 0;
  });
}

function usePageSize() {
  const [size, setSize] = useState(5);
  useEffect(() => {
    const update = () => setSize(window.innerWidth < 768 ? 3 : 5);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);
  return size;
}

export default function GuidesListPage() {
  const pageSize = usePageSize();
  const [allGuides, setAllGuides] = useState<GuideItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<SortKey>("date_desc");
  const { isProxyMode } = usePatient();

  useEffect(() => {
    api.listGuides().then((res) => {
      if (res.success && res.data) setAllGuides(res.data as GuideItem[]);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    setPage(1);
  }, [pageSize, sort]);

  const sortedGuides = useMemo(() => sortGuides(allGuides, sort), [allGuides, sort]);
  const totalPages = Math.max(1, Math.ceil(sortedGuides.length / pageSize));
  const pagedGuides = sortedGuides.slice((page - 1) * pageSize, page * pageSize);

  const thisMonthCount = allGuides.filter(
    (g) => new Date(g.created_at) >= new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  ).length;

  const pageNumbers = () => {
    const pages: number[] = [];
    const maxVisible = 5;
    let start = Math.max(1, page - Math.floor(maxVisible / 2));
    const end = Math.min(totalPages, start + maxVisible - 1);
    start = Math.max(1, end - maxVisible + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    return pages;
  };

  const handleDelete = async (guideId: number) => {
    if (!confirm("가이드를 삭제하시겠습니까?")) return;
    setDeletingId(guideId);
    const res = await api.deleteGuide(guideId);
    if (res.success) {
      setAllGuides((prev) => prev.filter((g) => g.id !== guideId));
    }
    setDeletingId(null);
  };

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold">가이드 기록</h1>
          <p style={{ color: 'var(--color-text-muted)' }}>이전에 생성된 복약 가이드를 확인하세요</p>
        </div>
        <Link href="/prescriptions/upload" className="px-4 py-2 rounded-lg btn-primary">
          가이드 생성
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="app-card rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{allGuides.length}</p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>총 가이드 수</p>
        </div>
        <div className="app-card rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{thisMonthCount}</p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>이번 달</p>
        </div>
        <div className="app-card rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{allGuides.length}</p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>완료됨</p>
        </div>
      </div>

      {loading ? (
        <p className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>로딩 중...</p>
      ) : allGuides.length === 0 ? (
        <p className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>아직 생성된 가이드가 없습니다.</p>
      ) : (
        <>
          {/* Sort */}
          <div className="flex gap-3 mb-4">
            <button
              onClick={() => setSort(sort === "date_desc" ? "date_asc" : "date_desc")}
              className="flex items-center gap-1 px-5 py-2.5 rounded-xl text-base font-semibold transition-colors"
              style={
                sort === "date_desc" || sort === "date_asc"
                  ? { background: 'var(--color-primary)', color: '#fff' }
                  : { background: 'var(--color-surface)', color: 'var(--color-text-muted)' }
              }
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg>
              날짜순 {sort === "date_desc" ? "↓" : sort === "date_asc" ? "↑" : "↓"}
            </button>
            <button
              onClick={() => setSort(sort === "name_asc" ? "name_desc" : "name_asc")}
              className="flex items-center gap-1 px-5 py-2.5 rounded-xl text-base font-semibold transition-colors"
              style={
                sort === "name_asc" || sort === "name_desc"
                  ? { background: 'var(--color-primary)', color: '#fff' }
                  : { background: 'var(--color-surface)', color: 'var(--color-text-muted)' }
              }
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M2.5 4v3h5v12h3V7h5V4h-13zm19 5h-9v3h9V9zm0 5h-9v3h9v-3zm0-10h-9v3h9V4z"/></svg>
              이름순 {sort === "name_asc" ? "↓" : sort === "name_desc" ? "↑" : ""}
            </button>
          </div>

          <div className="space-y-4">
            {pagedGuides.map((guide) => (
              <Link key={guide.id} href={`/guides/${guide.id}`} className="block app-card p-5">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ background: 'var(--color-primary-soft)' }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="var(--color-primary)"><path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z"/></svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold truncate">{guide.prescription_info.hospital_name || "병원명 미입력"}</h3>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                      <span>처방일 {guide.prescription_info.prescription_date}</span>
                      <span>담당의 {guide.prescription_info.doctor_name}</span>
                      <span>진단 {guide.prescription_info.diagnosis}</span>
                    </div>
                  </div>
                  <span className="flex-shrink-0" style={{ color: 'var(--color-text-muted)' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg>
                  </span>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-1 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-2 rounded-lg text-sm disabled:opacity-30 transition-colors"
                style={{ color: 'var(--color-text-muted)' }}
              >
                이전
              </button>
              {pageNumbers().map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className="w-9 h-9 rounded-lg text-sm font-medium transition-colors"
                  style={
                    p === page
                      ? { background: 'var(--color-primary)', color: '#fff' }
                      : { color: 'var(--color-text-muted)' }
                  }
                >
                  {p}
                </button>
              ))}
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-2 rounded-lg text-sm disabled:opacity-30 transition-colors"
                style={{ color: 'var(--color-text-muted)' }}
              >
                다음
              </button>
            </div>
          )}
        </>
      )}
    </AppLayout>
  );
}
