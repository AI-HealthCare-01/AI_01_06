"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { usePatient } from "@/lib/patient-context";
import type { PatientProfile } from "@/types/profile";

interface ProfileResponse {
  name: string;
  patient_profile: PatientProfile | null;
  is_proxy_view?: boolean;
}

export default function PatientHealthSummary() {
  const { activePatient, isProxyMode } = usePatient();
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isProxyMode) return;
    let cancelled = false;
    setLoading(true);
    api.getMe().then((res) => {
      if (cancelled) return;
      if (res.success) {
        const data = res.data as ProfileResponse;
        setProfile(data.patient_profile);
      }
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [isProxyMode, activePatient?.id]);

  if (!isProxyMode || !activePatient) return null;
  if (loading) {
    return (
      <div className="app-card p-4 mb-4 md:hidden animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
      </div>
    );
  }

  const p = profile;
  const hasAllergy = p?.has_allergy ?? false;
  const hasDisease = p?.has_disease ?? false;

  return (
    <div className="app-card p-4 mb-4 md:hidden">
      <h3
        className="text-sm font-bold mb-3"
        style={{ color: "var(--color-text)" }}
      >
        {activePatient.name}님의 건강 정보
      </h3>

      {/* 1행: 키 / 몸무게 */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div
          className="p-3 rounded-lg"
          style={{ background: "var(--color-surface)" }}
        >
          <span
            className="text-xs font-medium"
            style={{ color: "var(--color-text-muted)" }}
          >
            키
          </span>
          <p className="text-sm font-bold mt-0.5" style={{ color: "var(--color-text)" }}>
            {p?.height_cm != null ? `${p.height_cm} cm` : "미입력"}
          </p>
        </div>
        <div
          className="p-3 rounded-lg"
          style={{ background: "var(--color-surface)" }}
        >
          <span
            className="text-xs font-medium"
            style={{ color: "var(--color-text-muted)" }}
          >
            몸무게
          </span>
          <p className="text-sm font-bold mt-0.5" style={{ color: "var(--color-text)" }}>
            {p?.weight_kg != null ? `${p.weight_kg} kg` : "미입력"}
          </p>
        </div>
      </div>

      {/* 2행: 알러지 / 기저질환 */}
      <div className="grid grid-cols-2 gap-3">
        <div
          className="p-3 rounded-lg"
          style={{ background: "var(--color-surface)" }}
        >
          <div className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              aria-hidden="true"
              style={{
                background: hasAllergy
                  ? "var(--color-danger)"
                  : "var(--color-success, #22c55e)",
              }}
            />
            <span
              className="text-xs font-medium"
              style={{ color: "var(--color-text-muted)" }}
            >
              {hasAllergy ? "알러지" : "알러지 없음"}
            </span>
          </div>
          {hasAllergy && p?.allergy_details && (
            <p className="text-xs mt-1.5" style={{ color: "var(--color-text)" }}>
              {p.allergy_details}
            </p>
          )}
        </div>
        <div
          className="p-3 rounded-lg"
          style={{ background: "var(--color-surface)" }}
        >
          <div className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              aria-hidden="true"
              style={{
                background: hasDisease
                  ? "var(--color-warning, #f59e0b)"
                  : "var(--color-success, #22c55e)",
              }}
            />
            <span
              className="text-xs font-medium"
              style={{ color: "var(--color-text-muted)" }}
            >
              {hasDisease ? "기저질환" : "기저질환 없음"}
            </span>
          </div>
          {hasDisease && p?.disease_details && (
            <p className="text-xs mt-1.5" style={{ color: "var(--color-text)" }}>
              {p.disease_details}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
