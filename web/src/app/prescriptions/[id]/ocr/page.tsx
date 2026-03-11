"use client";

import { useEffect, useState, useCallback } from "react";
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
  const [processing, setProcessing] = useState(true);

  const pollOcrStatus = useCallback(async () => {
    const res = await api.getPrescription(prescriptionId);
    if (!res.success || !res.data) return;
    const pData = res.data as { ocr_status: string };
    if (pData.ocr_status === "ocr_completed" || pData.ocr_status === "guide_completed") {
      setProcessing(false);
      const ocrRes = await api.getOcr(prescriptionId);
      if (ocrRes.success && ocrRes.data) setData(ocrRes.data as OcrData);
    }
  }, [prescriptionId]);

  useEffect(() => {
    pollOcrStatus();
    const interval = setInterval(() => {
      if (processing) pollOcrStatus();
    }, 2000);
    return () => clearInterval(interval);
  }, [pollOcrStatus, processing]);

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

  const [loadingImg] = useState(() => {
    const idx = Math.floor(Math.random() * 16) + 1;
    const ext = idx === 1 ? "jpeg" : "jpg";
    return `/loading/loading_${idx}.${ext}`;
  });

  if (processing) {
    return (
      <div className="fixed inset-0 bg-[#f5f5f7] flex flex-col z-50">
        <div className="absolute top-8 left-0 right-0 text-center z-10 w-full">
          <h1 className="text-3xl font-bold text-gray-800 bg-white/70 px-6 py-2 rounded-full inline-block backdrop-blur-sm shadow-sm">
            처방전 분석 중
          </h1>
        </div>

        <div className="flex-1 w-full relative">
          <img
            src={loadingImg}
            alt="알쓸신약 로딩"
            className="absolute inset-0 w-full h-full object-contain p-4"
          />
        </div>

        <div className="pb-16 pt-8 text-center bg-white/80 backdrop-blur-md z-10 border-t border-gray-100 shadow-[0_-20px_25px_-5px_rgba(255,255,255,0.8)]">
          <p className="text-xl font-semibold text-gray-800">OCR로 처방전을 분석하고 있습니다...</p>
          <p className="text-gray-500 mt-2">지루하지 않게 잠시만 사진을 감상하며 기다려주세요</p>
        </div>
      </div>
    );
  }

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
              <input value={data.hospital_name || ""} onChange={(e) => setData({ ...data, hospital_name: e.target.value })} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="border rounded px-2 py-1 w-full placeholder:text-gray-400" />
            ) : (
              <p className="font-medium">{data.hospital_name || <span className="text-gray-400 italic">인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">담당의</p>
            {editing ? (
              <input value={data.doctor_name || ""} onChange={(e) => setData({ ...data, doctor_name: e.target.value })} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="border rounded px-2 py-1 w-full placeholder:text-gray-400" />
            ) : (
              <p className="font-medium">{data.doctor_name || <span className="text-gray-400 italic">인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">처방일</p>
            {editing ? (
              <input type="date" value={data.prescription_date || ""} onChange={(e) => setData({ ...data, prescription_date: e.target.value })} className="border rounded px-2 py-1 w-full" />
            ) : (
              <p className="font-medium">{data.prescription_date || <span className="text-gray-400 italic">인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">진단명</p>
            {editing ? (
              <input value={data.diagnosis || ""} onChange={(e) => setData({ ...data, diagnosis: e.target.value })} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="border rounded px-2 py-1 w-full placeholder:text-gray-400" />
            ) : (
              <p className="font-medium">{data.diagnosis || <span className="text-gray-400 italic">인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
            )}
          </div>
        </div>
        <p className="text-base font-semibold text-gray-600 mt-3">인식된 처방전 내용이 맞는지 반드시 확인해주세요. 맞지 않는 부분이 있으면 수정 버튼을 눌러 수정해주세요</p>
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
                <div>
                  <p className="text-xs text-gray-500">복용 방법</p>
                  {editing ? (
                    <input value={med.frequency} onChange={(e) => updateMed(i, "frequency", e.target.value)} className="border rounded px-2 py-1 w-full text-sm" />
                  ) : (
                    <p>{med.frequency}</p>
                  )}
                </div>
                <div>
                  <p className="text-xs text-gray-500">복용기간</p>
                  {editing ? (
                    <input value={med.duration || ""} onChange={(e) => updateMed(i, "duration", e.target.value)} className="border rounded px-2 py-1 w-full text-sm" />
                  ) : (
                    <p>{med.duration || "-"}</p>
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
