"use client";

import { useEffect, useState, useMemo } from "react";
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
              📅 날짜순 {sort === "date_desc" ? "↓" : sort === "date_asc" ? "↑" : "↓"}
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
              🔤 이름순 {sort === "name_asc" ? "↓" : sort === "name_desc" ? "↑" : ""}
            </button>
          </div>

          <div className="space-y-4">
            {pagedGuides.map((guide) => (
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
                    <button
                      onClick={() => handleDelete(guide.id)}
                      disabled={deletingId === guide.id}
                      className="text-sm border border-red-200 text-red-500 px-3 py-1 rounded hover:bg-red-50 disabled:opacity-50"
                    >
                      {deletingId === guide.id ? "삭제 중..." : "삭제"}
                    </button>
                  </div>
                </div>
              </div>
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
