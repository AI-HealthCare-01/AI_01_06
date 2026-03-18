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
      <div className="mb-6">
        <h1 className="text-2xl font-bold">안녕하세요, {user?.nickname}님</h1>
        {isProxyMode && activePatient ? (
          <p className="text-sm mt-1" style={{ color: "var(--color-primary)" }}>
            {activePatient.name}님의 건강 현황입니다
          </p>
        ) : (
          <p className="text-sm mt-0.5" style={{ color: "var(--color-text-muted)" }}>
            {today}
          </p>
        )}
      </div>

      <PatientHealthSummary />

      {scheduleError && (
        <p className="text-sm mb-4" style={{ color: "var(--color-danger)" }}>
          {scheduleError}
        </p>
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
