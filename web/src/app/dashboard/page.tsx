"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { usePatient } from "@/lib/patient-context";
import AppLayout from "@/components/AppLayout";
import TodayMedicationPanel from "@/components/dashboard/TodayMedicationPanel";
import FeatureQuickAccessPanel from "@/components/dashboard/FeatureQuickAccessPanel";
import RecentGuideListPanel from "@/components/dashboard/RecentGuideListPanel";
import PatientHealthSummary from "@/components/dashboard/PatientHealthSummary";
import { api, TodayScheduleItem } from "@/lib/api";

interface NotificationTimes {
  MORNING: string | null;
  NOON: string | null;
  EVENING: string | null;
  BEDTIME: string | null;
}

const DEFAULT_TIMES: NotificationTimes = {
  MORNING: "08:00",
  NOON: "12:00",
  EVENING: "18:00",
  BEDTIME: "22:00",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const { activePatient, isProxyMode } = usePatient();
  const [schedules, setSchedules] = useState<TodayScheduleItem[]>([]);
  const [loadingSchedules, setLoadingSchedules] = useState(true);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [notificationTimes, setNotificationTimes] = useState<NotificationTimes>(DEFAULT_TIMES);

  useEffect(() => {
    Promise.all([
      api.listTodaySchedules(),
      api.getNotificationSettings(),
    ]).then(([schedRes, settingsRes]) => {
      if (schedRes.success && schedRes.data) {
        setSchedules(schedRes.data);
      } else {
        setScheduleError(schedRes.error || "복약 스케줄을 불러오지 못했습니다.");
      }
      if (settingsRes.success && settingsRes.data) {
        const d = settingsRes.data as Record<string, string | null>;
        setNotificationTimes({
          MORNING: d.morning_time ?? "08:00",
          NOON: d.noon_time ?? "12:00",
          EVENING: d.evening_time ?? "18:00",
          BEDTIME: d.bedtime_time ?? "22:00",
        });
      }
      setLoadingSchedules(false);
    }).catch(() => {
      setScheduleError("서버에 연결할 수 없습니다.");
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
      {/* 인사말 영역 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold" style={{ color: "var(--color-text)" }}>
          안녕하세요, {user?.nickname}님
        </h1>
        {isProxyMode && activePatient ? (
          <div
            className="inline-flex items-center gap-2 mt-2 px-4 py-2 rounded-xl text-sm font-medium"
            style={{ background: "var(--color-primary-soft)", color: "var(--color-primary)" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>
            {activePatient.name}님의 건강 현황입니다
          </div>
        ) : (
          <div
            className="inline-flex items-center gap-2 mt-2 px-4 py-2 rounded-xl text-sm"
            style={{ background: "var(--color-surface)", color: "var(--color-text-muted)" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z"/></svg>
            {today}
          </div>
        )}
      </div>

      <PatientHealthSummary />

      {scheduleError && (
        <div className="alert-warning p-4 mb-6 text-sm">
          {scheduleError}
        </div>
      )}

      {loadingSchedules ? (
        <FeatureQuickAccessPanel loading />
      ) : hasActiveSchedules ? (
        <TodayMedicationPanel
          schedules={schedules}
          onSchedulesChange={setSchedules}
          notificationTimes={notificationTimes}
        />
      ) : (
        <FeatureQuickAccessPanel loading={false} />
      )}

      <RecentGuideListPanel />
    </AppLayout>
  );
}
