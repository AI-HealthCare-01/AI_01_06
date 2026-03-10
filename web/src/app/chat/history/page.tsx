"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface ThreadItem {
  id: number;
  title: string | null;
  prescription_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function ChatHistoryPage() {
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
          <h1 className="text-2xl font-bold">대화 기록</h1>
          <p className="text-gray-600">이전 AI 상담 내역을 확인하세요</p>
        </div>
        <Link
          href="/chat"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          새 상담 시작
        </Link>
      </div>

      {loading ? (
        <p className="text-gray-500 text-center py-8">로딩 중...</p>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center text-red-600">
          {error}
        </div>
      ) : threads.length === 0 ? (
        <div className="bg-white rounded-lg p-8 text-center text-gray-400 shadow-sm">
          아직 대화 기록이 없습니다.
        </div>
      ) : (
        <div className="space-y-4">
          {threads.map((thread) => (
            <Link
              key={thread.id}
              href={`/chat/${thread.id}`}
              className="block bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold truncate">
                      {thread.title || "제목 없음"}
                    </h3>
                    {thread.prescription_id && (
                      <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full whitespace-nowrap">
                        처방전 연결
                      </span>
                    )}
                  </div>
                  <div className="flex gap-4 text-sm text-gray-500 mt-1">
                    <span>{thread.created_at.slice(0, 10)}</span>
                    <span>
                      {thread.is_active ? "진행 중" : "종료됨"}
                    </span>
                  </div>
                </div>
                <span className="text-gray-400 text-sm ml-4">&gt;</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
