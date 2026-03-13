"use client";

import { api, TodayScheduleItem } from "@/lib/api";

interface Props {
  schedules: TodayScheduleItem[];
  onSchedulesChange: (updated: TodayScheduleItem[]) => void;
}

const TIME_LABEL: Record<string, string> = {
  MORNING: "아침",
  NOON: "점심",
  EVENING: "저녁",
  BEDTIME: "취침 전",
};

export default function TodayMedicationPanel({ schedules, onSchedulesChange }: Props) {
  const taken = schedules.filter((s) => s.today_status === "TAKEN").length;
  const total = schedules.length;
  const pct = total > 0 ? Math.round((taken / total) * 100) : 0;

  async function handleCheck(item: TodayScheduleItem) {
    if (item.today_status === "TAKEN") return;

    const optimistic = schedules.map((s) =>
      s.id === item.id ? { ...s, today_status: "TAKEN" as const } : s
    );
    onSchedulesChange(optimistic);

    const res = await api.logAdherence(item.id, "TAKEN");
    if (!res.success) onSchedulesChange(schedules);
  }

  return (
    <div
      className="app-card rounded-lg mb-6 overflow-hidden"
      style={{ borderTop: "4px solid var(--color-primary)" }}
    >
      {/* 헤더 */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold">오늘의 복약</h2>
          <span className="text-sm font-medium" style={{ color: "var(--color-primary)" }}>
            {taken} / {total}개 완료
          </span>
        </div>
        <div
          className="w-full rounded-full h-1.5 mt-2"
          style={{ background: "var(--color-border)" }}
        >
          <div
            className="h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, background: "var(--color-primary)" }}
          />
        </div>
      </div>

      {/* 약품 목록 */}
      <ul className="max-h-64 overflow-y-auto divide-y" style={{ borderColor: "var(--color-border)" }}>
        {schedules.map((item) => (
          <li key={item.id} className="flex items-center justify-between px-5 py-3">
            <div className="flex items-center gap-3 min-w-0">
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{
                  background:
                    item.today_status === "TAKEN"
                      ? "var(--color-success)"
                      : "var(--color-border)",
                }}
              />
              <div className="min-w-0">
                <p className="font-medium text-sm truncate">{item.medication_name}</p>
                <p className="text-xs mt-0.5 truncate" style={{ color: "var(--color-text-muted)" }}>
                  {[item.dosage, item.frequency, TIME_LABEL[item.time_of_day]]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </div>
            </div>
            <button
              onClick={() => handleCheck(item)}
              disabled={item.today_status === "TAKEN"}
              aria-label={`${item.medication_name} ${item.today_status === "TAKEN" ? "복약완료" : "복약하기"}`}
              aria-pressed={item.today_status === "TAKEN"}
              className="flex-shrink-0 ml-3 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200"
              style={
                item.today_status === "TAKEN"
                  ? { background: "var(--color-success)", color: "#fff", cursor: "default" }
                  : {
                      border: "1px solid var(--color-border)",
                      color: "var(--color-text-muted)",
                      background: "transparent",
                    }
              }
            >
              {item.today_status === "TAKEN" ? "✓ 복약완료" : "예정"}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
