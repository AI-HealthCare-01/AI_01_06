"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function OnboardingPage() {
  const { user, loading: authLoading, refreshUser } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    height_cm: "",
    weight_kg: "",
    has_allergy: false,
    allergy_details: "",
    has_disease: false,
    disease_details: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && user && user.role !== "PATIENT") {
      router.replace("/dashboard");
    }
  }, [user, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const res = await api.updateMe({
      height_cm: parseFloat(form.height_cm),
      weight_kg: parseFloat(form.weight_kg),
      has_allergy: form.has_allergy,
      allergy_details: form.has_allergy ? (form.allergy_details || null) : null,
      has_disease: form.has_disease,
      disease_details: form.has_disease ? (form.disease_details || null) : null,
    });
    if (!res.success) {
      setError(res.error || "저장에 실패했습니다.");
      setLoading(false);
      return;
    }
    await refreshUser();
    router.push("/dashboard");
  };

  if (authLoading || (user && user.role !== "PATIENT")) {
    return null;
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--color-bg)" }}>
      <Header />
      <div className="flex items-center justify-center py-10 px-4 pb-24 md:pb-10">
        <form
          onSubmit={handleSubmit}
          className="p-8 md:p-10 rounded-2xl w-full max-w-lg space-y-6"
          style={{
            background: "var(--color-card-bg)",
            boxShadow: "var(--shadow-lg)",
          }}
        >
          <div
            className="p-6 rounded-2xl text-white"
            style={{ background: "var(--color-primary)" }}
          >
            <h1 className="text-2xl font-bold">
              안녕하세요, {user?.name || "회원"}님!
            </h1>
            <p
              className="mt-1"
              style={{ color: "var(--color-surface-alt)" }}
            >
              저희 서비스를 이용하시기 전에 몇 가지 더 알려주세요.
            </p>
          </div>
          {error && (
            <p className="text-sm" style={{ color: "var(--color-danger)" }}>
              {error}
            </p>
          )}
          <h2 className="text-lg font-bold">사용자 정보</h2>
          <div
            className="rounded-2xl p-6 space-y-4"
            style={{ background: "var(--color-surface)" }}
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  키 (cm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  required
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
                  required
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
          </div>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="flex-1 py-2 rounded-lg btn-outline"
            >
              이전
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 btn-primary"
            >
              {loading ? "저장 중..." : "완료"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
