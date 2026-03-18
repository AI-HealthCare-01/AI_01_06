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
    <div
      className="app-card rounded-lg mb-6 overflow-hidden"
      style={{ borderTop: "4px solid var(--color-primary)" }}
    >
      {/* 헤더: 오늘의 복약 · {시간대} */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold">
            오늘의 복약{" "}
            <span className="font-normal text-sm" style={{ color: "var(--color-primary)" }}>
              · {TIME_LABEL[currentSlot]}
            </span>
          </h2>
          <span className="text-sm font-medium" style={{ color: "var(--color-primary)" }}>
            {taken} / {total}개 완료
          </span>
        </div>
        <div className="w-full rounded-full h-1.5 mt-2" style={{ background: "var(--color-border)" }}>
          <div
            className="h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, background: "var(--color-primary)" }}
          />
        </div>
      </div>

      {/* 캐러셀 영역 */}
      <div
        className="overflow-hidden"
        tabIndex={0}
        role="region"
        aria-label="시간대별 복약 캐러셀"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onKeyDown={(e) => {
          if (e.key === "ArrowRight" && currentPage < TIME_SLOTS.length - 1) setCurrentPage((p) => p + 1);
          if (e.key === "ArrowLeft" && currentPage > 0) setCurrentPage((p) => p - 1);
        }}
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
                  <div className="px-5 py-8 text-center">
                    <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                      {TIME_LABEL[slot]} 시간대에 복약이 없습니다.
                    </p>
                  </div>
                ) : (
                  <ul
                    className="max-h-64 overflow-y-auto divide-y"
                    style={{ borderColor: "var(--color-border)" }}
                  >
                    {items.map((item) => {
                      const isTaken = item.today_status === "TAKEN";
                      const mealInstr = getMealInstruction(item.instructions ?? null);
                      const subInfo = [item.frequency, mealInstr].filter(Boolean).join(" ");

                      return (
                        <li key={item.id} className="flex items-center justify-between px-5 py-3">
                          <div className="flex items-center gap-3 min-w-0">
                            <span
                              className="w-2 h-2 rounded-full flex-shrink-0"
                              style={{
                                background: isTaken ? "var(--color-success)" : "var(--color-border)",
                              }}
                            />
                            <div className="min-w-0">
                              <p className="font-medium text-sm truncate">
                                {item.medication_name}
                                {item.dosage && (
                                  <span
                                    className="font-normal ml-1"
                                    style={{ color: "var(--color-text-muted)" }}
                                  >
                                    {item.dosage}
                                  </span>
                                )}
                              </p>
                              {subInfo && (
                                <p
                                  className="text-xs mt-0.5 truncate"
                                  style={{ color: "var(--color-text-muted)" }}
                                >
                                  {subInfo}
                                </p>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => handleCheck(item)}
                            disabled={isTaken || !slotReached}
                            aria-label={`${item.medication_name} ${isTaken ? "복약완료" : slotReached ? "복약하기" : "예정"}`}
                            aria-pressed={isTaken}
                            className="flex-shrink-0 ml-3 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200"
                            style={
                              isTaken
                                ? { background: "var(--color-success)", color: "#fff", cursor: "default" }
                                : slotReached
                                  ? {
                                      border: "1px solid var(--color-border)",
                                      color: "var(--color-text-muted)",
                                      background: "transparent",
                                    }
                                  : {
                                      border: "1px solid var(--color-border)",
                                      color: "var(--color-text-muted)",
                                      background: "var(--color-surface)",
                                      opacity: 0.5,
                                      cursor: "not-allowed",
                                    }
                            }
                          >
                            {isTaken ? "✓ 복약완료" : "예정"}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 점 인디케이터 */}
      <div className="flex justify-center gap-2 py-3">
        {TIME_SLOTS.map((slot, i) => (
          <button
            key={slot}
            onClick={() => setCurrentPage(i)}
            aria-label={`${TIME_LABEL[slot]} 페이지`}
            aria-current={currentPage === i ? "true" : undefined}
            className="w-2 h-2 rounded-full transition-colors"
            style={{
              background: currentPage === i ? "var(--color-primary)" : "var(--color-border)",
            }}
          />
        ))}
      </div>
    </div>
  );
}
