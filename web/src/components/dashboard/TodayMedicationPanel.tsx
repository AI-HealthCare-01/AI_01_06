"use client";

import { useState, useEffect, useRef } from "react";
import { api, TodayScheduleItem } from "@/lib/api";

const TIME_SLOTS = ["MORNING", "NOON", "EVENING", "BEDTIME"] as const;
type TimeSlot = (typeof TIME_SLOTS)[number];

const TIME_LABEL: Record<TimeSlot, string> = {
  MORNING: "아침",
  NOON: "점심",
  EVENING: "저녁",
  BEDTIME: "자기전",
};

const TIME_ICON: Record<TimeSlot, React.ReactNode> = {
  MORNING: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0a.996.996 0 0 0 0-1.41l-1.06-1.06zm1.06-10.96a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z"/></svg>
  ),
  NOON: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/></svg>
  ),
  EVENING: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20 8.69V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69zM12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm0-10c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/></svg>
  ),
  BEDTIME: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12.01 12c0-3.57 2.2-6.62 5.31-7.87.89-.36.75-1.69-.19-1.9-1.1-.24-2.27-.18-3.37.21C10.07 3.83 7.43 7.21 7.84 11.2c.34 3.29 2.72 6.08 5.93 6.93 1.72.46 3.45.3 4.97-.3.89-.35 1.04-1.58.2-1.99C15.42 14.58 12.01 14.15 12.01 12z"/></svg>
  ),
};

interface Props {
  schedules: TodayScheduleItem[];
  onSchedulesChange: (updated: TodayScheduleItem[]) => void;
  notificationTimes: Record<TimeSlot, string | null>;
}

/** instructions 필드에서 식전/식후 추출 */
function getMealInstruction(instructions: string | null): string {
  if (!instructions) return "";
  if (instructions.includes("식전")) return "식전";
  if (instructions.includes("식후")) return "식후";
  return "";
}

/** 현재 시각 기준 캐러셀 초기 페이지 결정 (설정 시각 2시간 전 기준 이동) */
function getInitialPage(times: Record<TimeSlot, string | null>): number {
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();

  let result = TIME_SLOTS.length - 1; // 기본: BEDTIME

  for (let i = 0; i < TIME_SLOTS.length; i++) {
    const timeStr = times[TIME_SLOTS[i]];
    if (!timeStr) continue;
    const [h, m] = timeStr.split(":").map(Number);
    const threshold = h * 60 + m - 120; // 2시간 전
    if (currentMinutes >= threshold) {
      result = i;
    }
  }

  return result;
}

/** 해당 시간대의 설정 시각 도래 여부 */
function isTimeReached(slot: TimeSlot, times: Record<TimeSlot, string | null>): boolean {
  const timeStr = times[slot];
  if (!timeStr) return true;
  const [h, m] = timeStr.split(":").map(Number);
  const now = new Date();
  return now.getHours() > h || (now.getHours() === h && now.getMinutes() >= m);
}

export default function TodayMedicationPanel({ schedules, onSchedulesChange, notificationTimes }: Props) {
  const [currentPage, setCurrentPage] = useState(0);
  const touchStartX = useRef(0);

  useEffect(() => {
    setCurrentPage(getInitialPage(notificationTimes));
  }, [notificationTimes]);

  // 시간대별 스케줄 그룹핑
  const grouped: Record<TimeSlot, TodayScheduleItem[]> = {
    MORNING: schedules.filter((s) => s.time_of_day === "MORNING"),
    NOON: schedules.filter((s) => s.time_of_day === "NOON"),
    EVENING: schedules.filter((s) => s.time_of_day === "EVENING"),
    BEDTIME: schedules.filter((s) => s.time_of_day === "BEDTIME"),
  };

  // 전체 복약 진행률
  const taken = schedules.filter((s) => s.today_status === "TAKEN").length;
  const total = schedules.length;
  const pct = total > 0 ? Math.round((taken / total) * 100) : 0;
  const currentSlot = TIME_SLOTS[currentPage];

  async function handleCheck(item: TodayScheduleItem) {
    if (item.today_status === "TAKEN") return;
    const optimistic = schedules.map((s) =>
      s.id === item.id ? { ...s, today_status: "TAKEN" as const } : s,
    );
    onSchedulesChange(optimistic);
    const res = await api.logAdherence(item.id, "TAKEN");
    if (!res.success) onSchedulesChange(schedules);
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
      if (diff > 0 && currentPage < TIME_SLOTS.length - 1) setCurrentPage((p) => p + 1);
      if (diff < 0 && currentPage > 0) setCurrentPage((p) => p - 1);
    }
  };

  return (
    <section className="mb-8">
      {/* 섹션 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold" style={{ color: "var(--color-text)" }}>오늘의 복약</h2>
        <span
          className="text-sm font-semibold px-3 py-1 rounded-full"
          style={{ background: "var(--color-primary-soft)", color: "var(--color-primary)" }}
        >
          {taken}/{total} 완료
        </span>
      </div>

      {/* 진행률 바 */}
      <div
        className="w-full rounded-full h-2 mb-5"
        style={{ background: "var(--color-surface-alt)" }}
      >
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: "var(--color-primary)" }}
        />
      </div>

      {/* 시간대 탭 */}
      <div className="flex gap-2 mb-4">
        {TIME_SLOTS.map((slot, i) => {
          const isActive = currentPage === i;
          const slotItems = grouped[slot];
          const slotTaken = slotItems.filter((s) => s.today_status === "TAKEN").length;
          const slotTotal = slotItems.length;
          return (
            <button
              key={slot}
              onClick={() => setCurrentPage(i)}
              className="flex-1 flex flex-col items-center gap-1 py-3 rounded-2xl text-sm font-medium transition-all"
              style={
                isActive
                  ? { background: "var(--color-primary)", color: "#fff", boxShadow: "var(--shadow-md)" }
                  : { background: "var(--color-card-bg)", color: "var(--color-text-muted)", boxShadow: "var(--shadow-sm)" }
              }
            >
              <span style={{ color: isActive ? "#fff" : "var(--color-text-muted)" }}>{TIME_ICON[slot]}</span>
              <span>{TIME_LABEL[slot]}</span>
              {slotTotal > 0 && (
                <span className="text-xs" style={{ opacity: 0.8 }}>
                  {slotTaken}/{slotTotal}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* 캐러셀 영역 */}
      <div
        className="app-card overflow-hidden"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <div
          className="flex transition-transform duration-300 ease-out"
          style={{ transform: `translateX(-${currentPage * 100}%)` }}
        >
          {TIME_SLOTS.map((slot) => {
            const items = grouped[slot];
            const slotReached = isTimeReached(slot, notificationTimes);

            return (
              <div key={slot} className="w-full flex-shrink-0">
                {items.length === 0 ? (
                  <div className="px-6 py-12 text-center">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="var(--color-border)" className="mx-auto mb-3"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                    <p className="text-base" style={{ color: "var(--color-text-muted)" }}>
                      {TIME_LABEL[slot]} 시간대에 복약이 없습니다
                    </p>
                  </div>
                ) : (
                  <div className="divide-y" style={{ borderColor: "var(--color-surface)" }}>
                    {items.map((item) => {
                      const isTaken = item.today_status === "TAKEN";
                      const mealInstr = getMealInstruction(item.instructions ?? null);

                      return (
                        <div key={item.id} className="flex items-center justify-between px-6 py-4">
                          <div className="flex items-center gap-4 min-w-0 flex-1">
                            {/* 상태 아이콘 */}
                            <div
                              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                              style={{
                                background: isTaken ? "var(--color-success-soft)" : "var(--color-surface)",
                              }}
                            >
                              {isTaken ? (
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--color-success)"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                              ) : (
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--color-text-muted)"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/></svg>
                              )}
                            </div>
                            {/* 약 정보 */}
                            <div className="min-w-0">
                              <p className="text-base font-semibold truncate" style={{ color: "var(--color-text)" }}>
                                {item.medication_name}
                              </p>
                              <div className="flex items-center gap-2 mt-0.5">
                                {item.dosage && (
                                  <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                                    {item.dosage}
                                  </span>
                                )}
                                {mealInstr && (
                                  <span
                                    className="text-xs px-2 py-0.5 rounded-full font-medium"
                                    style={{ background: "var(--color-warning-soft)", color: "var(--color-warning-text)" }}
                                  >
                                    {mealInstr}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          {/* 복약 버튼 */}
                          <button
                            onClick={() => handleCheck(item)}
                            disabled={isTaken || !slotReached}
                            aria-label={`${item.medication_name} ${isTaken ? "복약완료" : slotReached ? "복약하기" : "예정"}`}
                            aria-pressed={isTaken}
                            className="flex-shrink-0 ml-3 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 whitespace-nowrap"
                            style={
                              isTaken
                                ? { background: "var(--color-success)", color: "#fff", cursor: "default" }
                                : slotReached
                                  ? {
                                      background: "var(--color-primary-pale)",
                                      color: "var(--color-primary)",
                                      cursor: "pointer",
                                    }
                                  : {
                                      background: "var(--color-surface)",
                                      color: "var(--color-text-muted)",
                                      opacity: 0.5,
                                      cursor: "not-allowed",
                                    }
                            }
                          >
                            {isTaken ? "완료" : slotReached ? "복약하기" : "예정"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 점 인디케이터 (모바일 전용 — 탭이 보이지 않는 경우 대비) */}
        <div className="flex items-center justify-center gap-3 py-3 md:hidden">
          {TIME_SLOTS.map((slot, i) => (
            <button
              key={slot}
              onClick={() => setCurrentPage(i)}
              aria-label={`${TIME_LABEL[slot]} 페이지`}
              aria-current={currentPage === i ? "true" : undefined}
              className="flex items-center justify-center w-11 h-11"
            >
              <span
                className="w-2 h-2 rounded-full transition-colors"
                style={{
                  background: currentPage === i ? "var(--color-primary)" : "var(--color-border)",
                }}
              />
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
