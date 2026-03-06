"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface Medication {
  id?: number;
  name: string;
  dosage: string;
  frequency: string;
  duration?: string;
  instructions?: string;
}

interface OcrData {
  hospital_name: string;
  doctor_name: string;
  prescription_date: string;
  diagnosis: string;
  medications: Medication[];
}

export default function OcrReviewPage() {
  const params = useParams();
  const router = useRouter();
  const prescriptionId = Number(params.id);
  const [data, setData] = useState<OcrData | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api.getOcr(prescriptionId).then((res) => {
      if (res.success && res.data) setData(res.data as OcrData);
    });
  }, [prescriptionId]);

  const handleSave = async () => {
    if (!data) return;
    setSaving(true);
    await api.updateOcr(prescriptionId, data);
    setEditing(false);
    setSaving(false);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    const res = await api.createGuide(prescriptionId);
    if (res.success && res.data) {
      const guideData = res.data as { id: number };
      router.push(`/guides/${guideData.id}`);
    }
  };

  const updateMed = (index: number, field: string, value: string) => {
    if (!data) return;
    const meds = [...data.medications];
    meds[index] = { ...meds[index], [field]: value };
    setData({ ...data, medications: meds });
  };

  const removeMed = (index: number) => {
    if (!data) return;
    setData({ ...data, medications: data.medications.filter((_, i) => i !== index) });
  };

  if (!data) {
    return <AppLayout><p className="text-gray-500">로딩 중...</p></AppLayout>;
  }

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-2">처방전 내용 확인</h1>
      <p className="text-gray-600 mb-4">처방전이 성공적으로 인식되었습니다. 내용을 확인하고 필요시 수정해주세요.</p>

      {/* Stepper */}
      <div className="flex items-center gap-2 mb-8">
        <div className="bg-gray-200 text-gray-500 px-4 py-2 rounded-full text-sm">처방전 올리기</div>
        <span className="text-gray-400">→</span>
        <div className="bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-medium">내용 확인</div>
        <span className="text-gray-400">→</span>
        <div className="bg-gray-200 text-gray-500 px-4 py-2 rounded-full text-sm">가이드 생성</div>
      </div>

      {/* Basic info */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-bold">기본 정보</h2>
          {!editing && (
            <button onClick={() => setEditing(true)} className="text-sm text-blue-600 hover:underline">수정</button>
          )}
        </div>
        <div className="bg-gray-100 rounded-lg p-6 grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">병원명</p>
            {editing ? (
              <input value={data.hospital_name} onChange={(e) => setData({ ...data, hospital_name: e.target.value })} className="border rounded px-2 py-1 w-full" />
            ) : (
              <p className="font-medium">{data.hospital_name}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">담당의</p>
            {editing ? (
              <input value={data.doctor_name} onChange={(e) => setData({ ...data, doctor_name: e.target.value })} className="border rounded px-2 py-1 w-full" />
            ) : (
              <p className="font-medium">{data.doctor_name}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">처방일</p>
            {editing ? (
              <input type="date" value={data.prescription_date} onChange={(e) => setData({ ...data, prescription_date: e.target.value })} className="border rounded px-2 py-1 w-full" />
            ) : (
              <p className="font-medium">{data.prescription_date}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">진단명</p>
            {editing ? (
              <input value={data.diagnosis} onChange={(e) => setData({ ...data, diagnosis: e.target.value })} className="border rounded px-2 py-1 w-full" />
            ) : (
              <p className="font-medium">{data.diagnosis}</p>
            )}
          </div>
        </div>
      </section>

      {/* Medications */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">처방 약물</h2>
        <div className="bg-gray-100 rounded-lg p-4 space-y-4">
          {data.medications.map((med, i) => (
            <div key={i} className="bg-white rounded-lg p-4 border relative">
              {editing && (
                <button onClick={() => removeMed(i)} className="absolute top-2 right-2 text-sm text-red-500 bg-gray-100 px-2 py-1 rounded hover:bg-red-50">
                  제거
                </button>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-gray-500">약품명</p>
                  {editing ? (
                    <input value={med.name} onChange={(e) => updateMed(i, "name", e.target.value)} className="border rounded px-2 py-1 w-full text-sm" />
                  ) : (
                    <p className="font-medium">{med.name}</p>
                  )}
                </div>
                <div>
                  <p className="text-xs text-gray-500">용량</p>
                  {editing ? (
                    <input value={med.dosage} onChange={(e) => updateMed(i, "dosage", e.target.value)} className="border rounded px-2 py-1 w-full text-sm" />
                  ) : (
                    <p>{med.dosage}</p>
                  )}
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-gray-500">복용 방법</p>
                  {editing ? (
                    <input value={med.frequency} onChange={(e) => updateMed(i, "frequency", e.target.value)} className="border rounded px-2 py-1 w-full text-sm" />
                  ) : (
                    <p>{med.frequency}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Buttons */}
      <div className="flex gap-4">
        <button onClick={() => router.push("/prescriptions/upload")} className="flex-1 border py-3 rounded-lg">
          이전 단계로
        </button>
        {editing ? (
          <button onClick={handleSave} disabled={saving} className="flex-1 bg-yellow-500 text-white py-3 rounded-lg hover:bg-yellow-600 disabled:opacity-50">
            {saving ? "저장 중..." : "수정"}
          </button>
        ) : null}
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {generating ? "생성 중..." : "가이드 생성 →"}
        </button>
      </div>
    </AppLayout>
  );
}
