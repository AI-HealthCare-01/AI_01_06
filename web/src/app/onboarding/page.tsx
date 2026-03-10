"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function OnboardingPage() {
  const { user, loading: authLoading, refreshUser } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ height_cm: "", weight_kg: "", allergy_details: "", disease_details: "" });
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
      height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
      weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
      allergy_details: form.allergy_details || null,
      disease_details: form.disease_details || null,
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
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex items-center justify-center py-10">
        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-sm w-full max-w-lg space-y-6">
          <div className="bg-gray-800 text-white p-6 rounded-lg">
            <h1 className="text-xl font-bold">안녕하세요, {user?.name || "회원"}님!</h1>
            <p className="text-gray-300 mt-1">저희 서비스를 이용하시기 전에 몇 가지 더 알려주세요.</p>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <h2 className="text-lg font-bold">사용자 정보</h2>
          <div className="bg-gray-100 rounded-lg p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">키 (cm)</label>
                <input type="number" step="0.1" value={form.height_cm} onChange={(e) => setForm({ ...form, height_cm: e.target.value })} className="w-full border rounded px-3 py-2" placeholder="175.8" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">몸무게 (kg)</label>
                <input type="number" step="0.1" value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} className="w-full border rounded px-3 py-2" placeholder="75.4" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">알러지 유무</label>
              <textarea value={form.allergy_details} onChange={(e) => setForm({ ...form, allergy_details: e.target.value })} className="w-full border rounded px-3 py-2" rows={2} placeholder="알러지가 있다면 입력해주세요" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">기저질환 유무</label>
              <textarea value={form.disease_details} onChange={(e) => setForm({ ...form, disease_details: e.target.value })} className="w-full border rounded px-3 py-2" rows={2} placeholder="기저질환이 있다면 입력해주세요" />
            </div>
          </div>
          <div className="flex gap-4">
            <button type="button" onClick={() => router.push("/dashboard")} className="flex-1 border py-2 rounded-lg">이전</button>
            <button type="submit" disabled={loading} className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {loading ? "저장 중..." : "완료"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
