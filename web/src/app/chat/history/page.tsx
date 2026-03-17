"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { usePatient } from "@/lib/patient-context";

interface ThreadItem {
  id: number;
  title: string | null;
  prescription_id: number | null;
  is_active: boolean;
  status: "active" | "auto_closed" | "ended";
  created_at: string;
  updated_at: string;
}

interface PaginatedThreads {
  threads: ThreadItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const STATUS_FILTERS = [
  { value: "all", label: "전체" },
  { value: "active", label: "진행 중" },
  { value: "ended", label: "종료됨" },
];

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

export default function ChatHistoryPage() {
  const { activePatient, isProxyMode } = usePatient();
  const pageSize = usePageSize();
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchThreads = useCallback((p: number, size: number, filterStatus: string) => {
    setLoading(true);
    setError(null);
    api
      .listThreads(p, size, filterStatus)
      .then((res) => {
        if (res.success && res.data) {
          const data = res.data as PaginatedThreads;
          setThreads(data.threads);
          setPage(data.page);
          setTotalPages(data.total_pages);
        } else {
          setError(res.error || "대화 기록을 불러오지 못했습니다.");
        }
      })
      .catch(() => {
        setError("서버 연결에 실패했습니다.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchThreads(1, pageSize, statusFilter);
  }, [pageSize, fetchThreads]);

  const handleFilterChange = (newFilter: string) => {
    setStatusFilter(newFilter);
    fetchThreads(1, pageSize, newFilter);
  };

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages) return;
    fetchThreads(newPage, pageSize, statusFilter);
  };

  const pageNumbers = () => {
    const pages: number[] = [];
    const maxVisible = 5;
    let start = Math.max(1, page - Math.floor(maxVisible / 2));
    const end = Math.min(totalPages, start + maxVisible - 1);
    start = Math.max(1, end - maxVisible + 1);
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">
            {isProxyMode && activePatient
              ? `${activePatient.name}님의 상담 기록`
              : "대화 기록"}
          </h1>
          <p style={{ color: "var(--color-text-muted)" }}>
            {isProxyMode && activePatient
              ? `${activePatient.name}님의 이전 AI 상담 내역입니다`
              : "이전 AI 상담 내역을 확인하세요"}
          </p>
        </div>
        <Link href="/chat" className="px-4 py-2 rounded-lg btn-primary">
          새 상담 시작
        </Link>
      </div>

      {/* Status Filter */}
      <div className="flex gap-2 mb-4">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => handleFilterChange(f.value)}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            style={
              statusFilter === f.value
                ? { background: "var(--color-primary)", color: "#fff" }
                : { background: "var(--color-surface)", color: "var(--color-text-muted)" }
            }
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-center py-8" style={{ color: "var(--color-text-muted)" }}>로딩 중...</p>
      ) : error ? (
        <div className="alert-danger rounded-lg p-8 text-center">{error}</div>
      ) : threads.length === 0 ? (
        <div className="app-card rounded-lg p-8 text-center" style={{ color: "var(--color-text-muted)" }}>
          {statusFilter === "all" ? "아직 대화 기록이 없습니다." : "해당 조건의 대화 기록이 없습니다."}
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {threads.map((thread) => (
              <Link key={thread.id} href={`/chat/${thread.id}`} className="block app-card rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold truncate">{thread.title || "제목 없음"}</h3>
                      {thread.prescription_id && (
                        <span
                          className="text-xs px-2 py-0.5 rounded-full whitespace-nowrap"
                          style={{ background: "var(--color-primary-soft)", color: "var(--color-primary)" }}
                        >
                          처방전 연결
                        </span>
                      )}
                    </div>
                    <div className="flex gap-4 text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
                      <span>{thread.created_at.slice(0, 10)}</span>
                      <span>{thread.status === "active" ? "진행 중" : "종료됨"}</span>
                    </div>
                  </div>
                  <span className="text-sm ml-4" style={{ color: "var(--color-text-muted)" }}>
                    &gt;
                  </span>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-1 mt-6">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page <= 1}
                className="px-3 py-2 rounded-lg text-sm disabled:opacity-30 transition-colors"
                style={{ color: "var(--color-text-muted)" }}
              >
                이전
              </button>
              {pageNumbers().map((p) => (
                <button
                  key={p}
                  onClick={() => handlePageChange(p)}
                  className="w-9 h-9 rounded-lg text-sm font-medium transition-colors"
                  style={
                    p === page
                      ? { background: "var(--color-primary)", color: "#fff" }
                      : { color: "var(--color-text-muted)" }
                  }
                >
                  {p}
                </button>
              ))}
              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page >= totalPages}
                className="px-3 py-2 rounded-lg text-sm disabled:opacity-30 transition-colors"
                style={{ color: "var(--color-text-muted)" }}
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
