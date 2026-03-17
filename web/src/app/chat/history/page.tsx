"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { usePatient } from "@/lib/patient-context";

interface ThreadItem {
  id: number;
  title: string | null;
  prescription_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function ChatHistoryPage() {
  const { activePatient, isProxyMode } = usePatient();
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listThreads()
      .then((res) => {
        if (res.success && res.data) {
          setThreads(res.data as ThreadItem[]);
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

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">
            {isProxyMode && activePatient
              ? `${activePatient.name}님의 상담 기록`
              : "대화 기록"}
          </h1>
          <p style={{ color: 'var(--color-text-muted)' }}>
            {isProxyMode && activePatient
              ? `${activePatient.name}님의 이전 AI 상담 내역입니다`
              : "이전 AI 상담 내역을 확인하세요"}
          </p>
        </div>
        <Link
          href="/chat"
          className="px-4 py-2 rounded-lg btn-primary"
        >
          새 상담 시작
        </Link>
      </div>

      {loading ? (
        <p className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>로딩 중...</p>
      ) : error ? (
        <div className="alert-danger rounded-lg p-8 text-center">
          {error}
        </div>
      ) : threads.length === 0 ? (
        <div className="app-card rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          아직 대화 기록이 없습니다.
        </div>
      ) : (
        <div className="space-y-4">
          {threads.map((thread) => (
            <Link
              key={thread.id}
              href={`/chat/${thread.id}`}
              className="block app-card rounded-lg p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold truncate">
                      {thread.title || "제목 없음"}
                    </h3>
                    {thread.prescription_id && (
                      <span className="text-xs px-2 py-0.5 rounded-full whitespace-nowrap" style={{ background: 'var(--color-primary-soft)', color: 'var(--color-primary)' }}>
                        처방전 연결
                      </span>
                    )}
                  </div>
                  <div className="flex gap-4 text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                    <span>{thread.created_at.slice(0, 10)}</span>
                    <span>
                      {thread.is_active ? "진행 중" : "종료됨"}
                    </span>
                  </div>
                </div>
                <span className="text-sm ml-4" style={{ color: 'var(--color-text-muted)' }}>&gt;</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
