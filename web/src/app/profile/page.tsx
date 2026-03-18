"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { PatientProfile } from "@/types/profile";

const TABS = ["info", "accessibility", "notification"] as const;
type Tab = (typeof TABS)[number];

interface ProfileData {
  email: string;
  name: string;
  role: string;
  has_password: boolean;
  patient_profile: PatientProfile | null;
}

type FontSize = "normal" | "large";

export default function ProfilePage() {
  const { user, loading: authLoading, logout } = useAuth();
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
  const [fontSize, setFontSize] = useState<FontSize>("large");
  const [message, setMessage] = useState("");

  // 알림 설정
  const [notiSettings, setNotiSettings] = useState({
    medication_enabled: true,
    caregiver_enabled: true,
    morning_time: "08:00",
    noon_time: "12:00",
    evening_time: "18:00",
    bedtime_time: "22:00",
  });
  const [notiLoading, setNotiLoading] = useState(false);
  const [notiMessage, setNotiMessage] = useState("");

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role === "PATIENT") {
      fetchProfile();
    }
  }, [user, authLoading, router]);

  // GUARDIAN은 개인정보 탭 불필요 — 접근성 설정만 표시
  useEffect(() => {
    if (user && user.role !== "PATIENT") setActiveTab("accessibility");
  }, [user]);

  useEffect(() => {
    const saved = (localStorage.getItem("fontSize") as FontSize) ?? "large";
    setFontSize(saved);

    const handler = (e: Event) => {
      const size = (e as CustomEvent).detail.size as FontSize;
      setFontSize(size);
    };
    window.addEventListener("fontSizeChanged", handler);
    return () => window.removeEventListener("fontSizeChanged", handler);
  }, []);

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

  const fetchNotificationSettings = async () => {
    setNotiLoading(true);
    const res = await api.getNotificationSettings();
    if (res.success && res.data) {
      const d = res.data as Record<string, unknown>;
      setNotiSettings({
        medication_enabled: (d.medication_enabled as boolean) ?? true,
        caregiver_enabled: (d.caregiver_enabled as boolean) ?? true,
        morning_time: (d.morning_time as string) ?? "08:00",
        noon_time: (d.noon_time as string) ?? "12:00",
        evening_time: (d.evening_time as string) ?? "18:00",
        bedtime_time: (d.bedtime_time as string) ?? "22:00",
      });
    }
    // res.data가 null이면 기본값 유지 (신규 유저)
    setNotiLoading(false);
  };

  useEffect(() => {
    if (activeTab === "notification") {
      fetchNotificationSettings();
    }
  }, [activeTab]);

  const handleNotiSave = async (field: string, value: unknown, prev: typeof notiSettings) => {
    const res = await api.updateNotificationSettings({ [field]: value });
    if (res.success) {
      setNotiMessage("저장되었습니다.");
      setTimeout(() => setNotiMessage(""), 2000);
    } else {
      setNotiSettings(prev);
    }
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

  const handleFontSize = async (size: FontSize) => {
    setFontSize(size);
    document.documentElement.setAttribute("data-font-size", size);
    localStorage.setItem("fontSize", size);
    window.dispatchEvent(new CustomEvent("fontSizeChanged", { detail: { size } }));
    await api.updateMe({ font_size_mode: size });
  };

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const handleDeleteAccount = async () => {
    setMessage("");
    if (profileData?.has_password) {
      const password = window.prompt("회원 탈퇴를 위해 비밀번호를 입력해주세요.");
      if (!password) return;

      const res = await api.deleteMe({ password });
      if (res.success) {
        logout();
        router.push("/");
      } else {
        setMessage(res.error || "탈퇴에 실패했습니다.");
      }
    } else {
      const email = window.prompt(
        "소셜 계정 탈퇴를 위해 가입 시 사용한 이메일을 입력해주세요."
      );
      if (!email) return;

      const res = await api.deleteMe({ confirm_email: email });
      if (res.success) {
        logout();
        router.push("/");
      } else {
        setMessage(res.error || "탈퇴에 실패했습니다.");
      }
    }
  };

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
            {isPatient ? (profileData?.name ?? user.name) : user.name}
          </h1>
          <p
            className="text-sm mt-0.5"
            style={{ color: "var(--color-text-muted)" }}
          >
            {isPatient ? (profileData?.email ?? user.email) : user.email}
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
        aria-label="프로필 설정"
        className="flex border-b mt-4"
        style={{ borderColor: "var(--color-border)" }}
      >
        {isPatient && (
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
        )}
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
        <button
          role="tab"
          aria-selected={activeTab === "notification"}
          tabIndex={activeTab === "notification" ? 0 : -1}
          id="tab-notification"
          aria-controls="panel-notification"
          onClick={() => setActiveTab("notification")}
          onKeyDown={handleTabKeyDown}
          className="px-4 py-2 text-sm font-medium transition-colors"
          style={{
            color:
              activeTab === "notification"
                ? "var(--color-primary)"
                : "var(--color-text-muted)",
            borderBottom:
              activeTab === "notification"
                ? "2px solid var(--color-primary)"
                : "2px solid transparent",
          }}
        >
          알림 설정
        </button>
      </div>

      {/* 개인정보 탭 */}
      {activeTab === "info" && (
        <div
          role="tabpanel"
          id="panel-info"
          aria-labelledby="tab-info"
          tabIndex={0}
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
          tabIndex={0}
          className="app-card p-6 mt-4"
        >
          <h3 className="text-sm font-medium" style={{ color: "var(--color-text)" }}>
            글자 크기
          </h3>
          <div className="flex gap-3 mt-3">
            <button
              onClick={() => handleFontSize("normal")}
              className="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
              style={
                fontSize === "normal"
                  ? { backgroundColor: "var(--color-primary)", color: "#fff" }
                  : { backgroundColor: "var(--color-surface)", color: "var(--color-text-muted)", border: "1px solid var(--color-border)" }
              }
            >
              일반
            </button>
            <button
              onClick={() => handleFontSize("large")}
              className="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
              style={
                fontSize === "large"
                  ? { backgroundColor: "var(--color-primary)", color: "#fff" }
                  : { backgroundColor: "var(--color-surface)", color: "var(--color-text-muted)", border: "1px solid var(--color-border)" }
              }
            >
              큰글씨
            </button>
          </div>
          <p className="text-xs mt-2" style={{ color: "var(--color-text-muted)" }}>
            선택한 글자 크기가 로그인 시 기본 설정으로 적용됩니다.
          </p>
        </div>
      )}

      {/* 알림 설정 탭 */}
      {activeTab === "notification" && (
        <div
          role="tabpanel"
          id="panel-notification"
          aria-labelledby="tab-notification"
          tabIndex={0}
          className="space-y-6 mt-4"
        >
          {notiLoading ? (
            <div className="app-card p-6">
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>불러오는 중...</p>
            </div>
          ) : (
            <>
              {/* 알림 유형 */}
              <div className="app-card p-6">
                <h3 className="text-sm font-bold mb-4" style={{ color: "var(--color-text)" }}>
                  알림 유형
                </h3>

                {/* 복약 알림 */}
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium" style={{ color: "var(--color-text)" }}>복약알림</p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--color-text-muted)" }}>
                      약 복용 시간을 알려드립니다.
                    </p>
                  </div>
                  <button
                    role="switch"
                    aria-checked={notiSettings.medication_enabled}
                    aria-label="복약 알림 켜기/끄기"
                    onClick={() => {
                      const prev = notiSettings;
                      const next = !notiSettings.medication_enabled;
                      setNotiSettings({ ...notiSettings, medication_enabled: next });
                      handleNotiSave("medication_enabled", next, prev);
                    }}
                    className="w-11 h-6 rounded-full transition-colors relative cursor-pointer"
                    style={{
                      backgroundColor: notiSettings.medication_enabled
                        ? "var(--color-primary)"
                        : "var(--color-border)",
                    }}
                  >
                    <span
                      className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform"
                      style={{
                        transform: notiSettings.medication_enabled ? "translateX(20px)" : "translateX(0)",
                      }}
                    />
                  </button>
                </div>

                <hr style={{ borderColor: "var(--color-border)" }} />

                {/* 보호자/돌봄대상 알림 */}
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium" style={{ color: "var(--color-text)" }}>
                      {isPatient ? "보호자 알림" : "돌봄대상 알림"}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--color-text-muted)" }}>
                      {isPatient
                        ? "보호자 활동 및 메시지를 알려드립니다."
                        : "돌봄대상 활동 및 메시지를 알려드립니다."}
                    </p>
                  </div>
                  <button
                    role="switch"
                    aria-checked={notiSettings.caregiver_enabled}
                    aria-label={isPatient ? "보호자 알림 켜기/끄기" : "돌봄대상 알림 켜기/끄기"}
                    onClick={() => {
                      const prev = notiSettings;
                      const next = !notiSettings.caregiver_enabled;
                      setNotiSettings({ ...notiSettings, caregiver_enabled: next });
                      handleNotiSave("caregiver_enabled", next, prev);
                    }}
                    className="w-11 h-6 rounded-full transition-colors relative cursor-pointer"
                    style={{
                      backgroundColor: notiSettings.caregiver_enabled
                        ? "var(--color-primary)"
                        : "var(--color-border)",
                    }}
                  >
                    <span
                      className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform"
                      style={{
                        transform: notiSettings.caregiver_enabled ? "translateX(20px)" : "translateX(0)",
                      }}
                    />
                  </button>
                </div>
              </div>

              {/* 시간 설정 */}
              <div className="app-card p-6">
                <h3 className="text-sm font-bold mb-4" style={{ color: "var(--color-text)" }}>
                  시간 설정
                </h3>
                {([
                  { key: "morning_time", label: "아침" },
                  { key: "noon_time", label: "점심" },
                  { key: "evening_time", label: "저녁" },
                  { key: "bedtime_time", label: "자기전" },
                ] as const).map(({ key, label }) => (
                  <div key={key} className="flex items-center justify-between py-3">
                    <span className="text-sm font-medium" style={{ color: "var(--color-text)" }}>
                      {label}
                    </span>
                    <input
                      type="time"
                      value={notiSettings[key] ?? ""}
                      onChange={(e) => {
                        setNotiSettings({ ...notiSettings, [key]: e.target.value });
                      }}
                      onBlur={(e) => {
                        handleNotiSave(key, e.target.value, notiSettings);
                      }}
                      className="px-3 py-1.5 rounded-lg text-sm input-field"
                      style={{ width: "120px" }}
                    />
                  </div>
                ))}
              </div>

              {/* 저장 메시지 */}
              {notiMessage && (
                <p className="text-sm" style={{ color: "var(--color-primary)" }}>{notiMessage}</p>
              )}
            </>
          )}
        </div>
      )}

      {/* 최하단: 로그아웃 + 회원탈퇴 */}
      <div className="mt-8 pt-6 flex gap-4" style={{ borderTop: "1px solid var(--color-border)" }}>
        <button
          onClick={handleLogout}
          className="flex-1 py-2 text-sm font-medium rounded-lg btn-outline"
        >
          로그아웃
        </button>
        <button
          onClick={handleDeleteAccount}
          className="flex-1 py-2 text-sm font-medium rounded-lg"
          style={{ color: "var(--color-danger)", border: "1px solid var(--color-danger)" }}
        >
          회원탈퇴
        </button>
      </div>
      {message && (
        <p className="text-sm mt-2" style={{ color: "var(--color-danger)" }}>
          {message}
        </p>
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
