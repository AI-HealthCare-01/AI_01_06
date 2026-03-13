"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import AppLayout from "@/components/AppLayout";
import TodayMedicationPanel from "@/components/dashboard/TodayMedicationPanel";
import FeatureQuickAccessPanel from "@/components/dashboard/FeatureQuickAccessPanel";
import RecentGuideListPanel from "@/components/dashboard/RecentGuideListPanel";
import { api, TodayScheduleItem } from "@/lib/api";

export default function DashboardPage() {
  const { user } = useAuth();
  const [schedules, setSchedules] = useState<TodayScheduleItem[]>([]);
  const [loadingSchedules, setLoadingSchedules] = useState(true);

  useEffect(() => {
    api.listTodaySchedules().then((res) => {
      if (res.success && res.data) setSchedules(res.data);
      setLoadingSchedules(false);
    });
  }, []);

  const hasActiveSchedules = !loadingSchedules && schedules.length > 0;
  const today = new Date().toLocaleDateString("ko-KR", {
    month: "long",
    day: "numeric",
    weekday: "short",
  });

  return (
    <AppLayout>
      {/* 인사 헤더 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">안녕하세요, {user?.nickname}님</h1>
        <p className="text-sm mt-0.5" style={{ color: "var(--color-text-muted)" }}>
          {today}
        </p>
      </div>

      {/* 조건부 상단 패널 */}
      {loadingSchedules ? (
        <FeatureQuickAccessPanel loading />
      ) : hasActiveSchedules ? (
        <TodayMedicationPanel schedules={schedules} onSchedulesChange={setSchedules} />
      ) : (
        <FeatureQuickAccessPanel loading={false} />
      )}

      {/* 공통 하단 패널 */}
      <RecentGuideListPanel />
    </AppLayout>
  );
}
