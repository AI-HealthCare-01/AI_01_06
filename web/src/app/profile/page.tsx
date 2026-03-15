"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const TABS = ["info", "accessibility"] as const;
type Tab = (typeof TABS)[number];

interface PatientProfile {
  height_cm: number | null;
  weight_kg: number | null;
  has_allergy: boolean;
  allergy_details: string | null;
  has_disease: boolean;
  disease_details: string | null;
}

interface ProfileData {
  email: string;
  name: string;
  role: string;
  patient_profile: PatientProfile | null;
}

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("info");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    height_cm: "",
    weight_kg: "",
    has_allergy: false,
    allergy_details: "",
    has_disease: false,
    disease_details: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    fetchProfile();
  }, [user, authLoading, router]);

  const fetchProfile = async () => {
    const res = await api.getMe();
    if (res.success) {
      const data = res.data as ProfileData;
      setProfileData(data);
      syncFormFromProfile(data.patient_profile);
    }
  };

  const syncFormFromProfile = (profile: PatientProfile | null) => {
    if (!profile) return;
    setForm({
      height_cm: profile.height_cm != null ? String(profile.height_cm) : "",
      weight_kg: profile.weight_kg != null ? String(profile.weight_kg) : "",
      has_allergy: profile.has_allergy,
      allergy_details: profile.allergy_details ?? "",
      has_disease: profile.has_disease,
      disease_details: profile.disease_details ?? "",
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    const res = await api.updateMe({
      height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
      weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
      has_allergy: form.has_allergy,
      allergy_details: form.has_allergy ? (form.allergy_details || null) : null,
      has_disease: form.has_disease,
      disease_details: form.has_disease ? (form.disease_details || null) : null,
    });
    if (!res.success) {
      setError(res.error || "저장에 실패했습니다.");
      setSaving(false);
      return;
    }
    await fetchProfile();
    setEditing(false);
    setSaving(false);
  };

  const handleCancel = () => {
    syncFormFromProfile(profileData?.patient_profile ?? null);
    setEditing(false);
    setError("");
  };

  const handleTabKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const idx = TABS.indexOf(activeTab);
      if (e.key === "ArrowRight") {
        e.preventDefault();
        setActiveTab(TABS[(idx + 1) % TABS.length]);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        setActiveTab(TABS[(idx - 1 + TABS.length) % TABS.length]);
      }
    },
    [activeTab],
  );

  if (authLoading || !user) return null;

  const profile = profileData?.patient_profile;
  const isPatient = user.role === "PATIENT";

  return (
    <AppLayout>
      {/* 상단 패널 */}
      <div
        className="app-card p-6 flex items-start justify-between"
      >
        <div>
          <h1
            className="text-lg font-bold"
            style={{ color: "var(--color-text)" }}
          >
            {profileData?.name ?? user.name}
          </h1>
          <p
            className="text-sm mt-0.5"
            style={{ color: "var(--color-text-muted)" }}
          >
            {profileData?.email ?? user.email}
          </p>
          <span
            className="inline-block mt-1 px-2 py-0.5 text-xs rounded-full"
            style={{
              background: "var(--color-surface)",
              color: "var(--color-text-muted)",
            }}
          >
            본인
          </span>
        </div>
        <span
          className="px-3 py-1 text-xs font-medium rounded-full"
          style={{
            background: "var(--color-primary-soft)",
            color: "var(--color-primary)",
          }}
        >
          {isPatient ? "일반" : "보호자"}
        </span>
      </div>

      {/* 탭 바 */}
      <div
        role="tablist"
        className="flex border-b mt-4"
        style={{ borderColor: "var(--color-border)" }}
      >
        <button
          role="tab"
          aria-selected={activeTab === "info"}
          tabIndex={activeTab === "info" ? 0 : -1}
          id="tab-info"
          aria-controls="panel-info"
          onClick={() => setActiveTab("info")}
          onKeyDown={handleTabKeyDown}
          className="px-4 py-2 text-sm font-medium transition-colors"
          style={{
            color:
              activeTab === "info"
                ? "var(--color-primary)"
                : "var(--color-text-muted)",
            borderBottom:
              activeTab === "info"
                ? "2px solid var(--color-primary)"
                : "2px solid transparent",
          }}
        >
          개인정보
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "accessibility"}
          tabIndex={activeTab === "accessibility" ? 0 : -1}
          id="tab-accessibility"
          aria-controls="panel-accessibility"
          onClick={() => setActiveTab("accessibility")}
          onKeyDown={handleTabKeyDown}
          className="px-4 py-2 text-sm font-medium transition-colors"
          style={{
            color:
              activeTab === "accessibility"
                ? "var(--color-primary)"
                : "var(--color-text-muted)",
            borderBottom:
              activeTab === "accessibility"
                ? "2px solid var(--color-primary)"
                : "2px solid transparent",
          }}
        >
          접근성 설정
        </button>
      </div>

      {/* 개인정보 탭 */}
      {activeTab === "info" && (
        <div
          role="tabpanel"
          id="panel-info"
          aria-labelledby="tab-info"
          className="app-card p-6 mt-4"
        >
          {isPatient ? (
            editing ? (
              /* 수정 모드 */
              <div className="space-y-4">
                {error && (
                  <p
                    className="text-sm"
                    style={{ color: "var(--color-danger)" }}
                  >
                    {error}
                  </p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      키 (cm)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min={50}
                      max={300}
                      value={form.height_cm}
                      onChange={(e) =>
                        setForm({ ...form, height_cm: e.target.value })
                      }
                      className="w-full px-3 py-2 input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      몸무게 (kg)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min={10}
                      max={500}
                      value={form.weight_kg}
                      onChange={(e) =>
                        setForm({ ...form, weight_kg: e.target.value })
                      }
                      className="w-full px-3 py-2 input-field"
                    />
                  </div>
                </div>
                <div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.has_allergy}
                      onChange={(e) =>
                        setForm({ ...form, has_allergy: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-medium">
                      알러지가 있습니다
                    </span>
                  </label>
                  {form.has_allergy && (
                    <textarea
                      value={form.allergy_details}
                      onChange={(e) =>
                        setForm({ ...form, allergy_details: e.target.value })
                      }
                      className="w-full px-3 py-2 input-field mt-2"
                      rows={2}
                      maxLength={1000}
                      placeholder="알러지 정보를 입력해주세요"
                    />
                  )}
                </div>
                <div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.has_disease}
                      onChange={(e) =>
                        setForm({ ...form, has_disease: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-medium">
                      기저질환이 있습니다
                    </span>
                  </label>
                  {form.has_disease && (
                    <textarea
                      value={form.disease_details}
                      onChange={(e) =>
                        setForm({ ...form, disease_details: e.target.value })
                      }
                      className="w-full px-3 py-2 input-field mt-2"
                      rows={2}
                      maxLength={1000}
                      placeholder="기저질환 정보를 입력해주세요"
                    />
                  )}
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 btn-primary text-sm"
                  >
                    {saving ? "저장 중..." : "변경사항 저장"}
                  </button>
                  <button
                    onClick={handleCancel}
                    disabled={saving}
                    className="px-4 py-2 btn-outline text-sm rounded-lg"
                  >
                    취소
                  </button>
                </div>
              </div>
            ) : (
              /* 읽기 모드 */
              <div className="relative">
                <button
                  onClick={() => setEditing(true)}
                  className="absolute top-0 right-0 text-sm px-3 py-1 rounded-lg btn-outline"
                >
                  수정
                </button>
                <div className="space-y-3 pr-16">
                  <InfoRow
                    label="키"
                    value={
                      profile?.height_cm != null
                        ? `${profile.height_cm} cm`
                        : "미입력"
                    }
                  />
                  <InfoRow
                    label="몸무게"
                    value={
                      profile?.weight_kg != null
                        ? `${profile.weight_kg} kg`
                        : "미입력"
                    }
                  />
                  <InfoRow
                    label="알러지"
                    value={
                      profile?.has_allergy
                        ? (profile.allergy_details ?? "있음")
                        : "없음"
                    }
                  />
                  <InfoRow
                    label="기저질환"
                    value={
                      profile?.has_disease
                        ? (profile.disease_details ?? "있음")
                        : "없음"
                    }
                  />
                </div>
              </div>
            )
          ) : (
            <p style={{ color: "var(--color-text-muted)" }}>
              준비 중인 기능입니다.
            </p>
          )}
        </div>
      )}

      {/* 접근성 설정 탭 */}
      {activeTab === "accessibility" && (
        <div
          role="tabpanel"
          id="panel-accessibility"
          aria-labelledby="tab-accessibility"
          className="app-card p-6 mt-4"
        >
          <p style={{ color: "var(--color-text-muted)" }}>
            준비 중인 기능입니다.
          </p>
        </div>
      )}
    </AppLayout>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-3">
      <span
        className="text-sm font-medium w-16 shrink-0"
        style={{ color: "var(--color-text-muted)" }}
      >
        {label}
      </span>
      <span className="text-sm" style={{ color: "var(--color-text)" }}>
        {value}
      </span>
    </div>
  );
}
