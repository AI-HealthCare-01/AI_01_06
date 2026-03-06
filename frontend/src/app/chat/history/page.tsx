"use client";

import AppLayout from "@/components/AppLayout";

export default function ChatHistoryPage() {
  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-6">이전 대화 리스트</h1>
      <div className="bg-white rounded-lg p-8 text-center text-gray-400 shadow-sm">
        아직 대화 기록이 없습니다.
      </div>
    </AppLayout>
  );
}
