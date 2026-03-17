"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { usePatient } from "@/lib/patient-context";

interface PatientProfile {
  height_cm: number | null;
  weight_kg: number | null;
  has_allergy: boolean;
  allergy_details: string | null;
  has_disease: boolean;
  disease_details: string | null;
}

interface ProxyProfileData {
  name: string;
  nickname: string;
  role: string;
  birth_date: string | null;
  gender: string | null;
  patient_profile: PatientProfile | null;
  is_proxy_view: boolean;
  guardian_name: string;
}

export default function ProxyProfilePage() {
  const { activePatient, isProxyMode } = usePatient();
  const router = useRouter();
  const [profileData, setProfileData] = useState<ProxyProfileData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isProxyMode) {
      router.replace("/caregivers");
      return;
    }
    api.getMe().then((res) => {
      if (res.success) {
        setProfileData(res.data as ProxyProfileData);
      }
      setLoading(false);
    });
  }, [isProxyMode, activePatient?.id, router]);

  if (!isProxyMode || !activePatient) return null;
  if (loading) return <AppLayout><div className="animate-pulse p-6" /></AppLayout>;

  const profile = profileData?.patient_profile;

  return (
    <AppLayout>
      <div className="max-w-lg mx-auto">
        {/* 상단 헤더 */}
        <div
          className="p-6 rounded-lg text-white mb-6"
          style={{ background: "var(--color-text)" }}
        >
          <h1 className="text-xl font-bold">{profileData?.name}님의 건강 정보</h1>
          <p className="mt-1" style={{ color: "var(--color-surface-alt)" }}>
            돌봄 대상의 건강 프로필을 확인하고 있습니다.
          </p>
        </div>

        {/* 프로필 카드 */}
        <div
          className="rounded-lg p-6 space-y-5"
          style={{
            background: "var(--color-card-bg)",
            border: "1px solid var(--color-border)",
            boxShadow: "0 1px 3px rgba(45,42,38,0.06)",
          }}
        >
          <h2 className="text-lg font-bold" style={{ color: "var(--color-text)" }}>
            건강 정보
          </h2>

          <div
            className="rounded-lg p-4 space-y-4"
            style={{ background: "var(--color-surface)" }}
          >
            {/* 키 / 몸무게 */}
            <div className="grid grid-cols-2 gap-4">
              <ReadOnlyField label="키 (cm)" value={profile?.height_cm != null ? String(profile.height_cm) : "미입력"} />
              <ReadOnlyField label="몸무게 (kg)" value={profile?.weight_kg != null ? String(profile.weight_kg) : "미입력"} />
            </div>

            {/* 알러지 */}
            <div>
              <StatusField label="알러지" hasCondition={profile?.has_allergy ?? false} />
              {profile?.has_allergy && profile.allergy_details && (
                <ReadOnlyTextArea value={profile.allergy_details} />
              )}
            </div>

            {/* 기저질환 */}
            <div>
              <StatusField label="기저질환" hasCondition={profile?.has_disease ?? false} />
              {profile?.has_disease && profile.disease_details && (
                <ReadOnlyTextArea value={profile.disease_details} />
              )}
            </div>
          </div>

          {/* 안내 문구 */}
          <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
            건강 정보의 수정은 {profileData?.name}님 본인만 가능합니다.
          </p>
        </div>
      </div>
    </AppLayout>
  );
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1" style={{ color: "var(--color-text)" }}>
        {label}
      </label>
      <div
        className="w-full px-3 py-2 rounded-lg text-sm"
        style={{
          background: "var(--color-bg)",
          border: "1px solid var(--color-border)",
          color: "var(--color-text)",
        }}
      >
        {value}
      </div>
    </div>
  );
}

function StatusField({ label, hasCondition }: { label: string; hasCondition: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="w-3 h-3 rounded-full"
        style={{
          background: hasCondition ? "var(--color-danger)" : "var(--color-success, #22c55e)",
        }}
      />
      <span className="text-sm font-medium" style={{ color: "var(--color-text)" }}>
        {hasCondition ? `${label} 있음` : `${label} 없음`}
      </span>
    </div>
  );
}

function ReadOnlyTextArea({ value }: { value: string }) {
  return (
    <div
      className="w-full px-3 py-2 rounded-lg text-sm mt-2"
      style={{
        background: "var(--color-bg)",
        border: "1px solid var(--color-border)",
        color: "var(--color-text)",
        minHeight: "3rem",
        whiteSpace: "pre-wrap",
      }}
    >
      {value}
    </div>
  );
}
