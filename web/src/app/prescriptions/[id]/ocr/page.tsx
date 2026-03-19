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

interface DiagnosisEntry {
  code?: string;
  label: string;
  isSupplementary: boolean;
}

const SUPPLEMENTARY_PREFIXES = new Set(["Z", "V", "W", "X", "Y"]);

function parseDiagnosis(diagnosis: string): DiagnosisEntry[] {
  if (!diagnosis.trim()) return [];

  const parseOnePart = (part: string): DiagnosisEntry => {
    const codeMatch = part.trim().match(/^([A-Z]\d{2}(?:\.\d+)?)\s*(.*)/);
    if (codeMatch) {
      const code = codeMatch[1];
      const label = codeMatch[2].trim() || code;
      return { code, label, isSupplementary: SUPPLEMENTARY_PREFIXES.has(code[0]) };
    }
    return { label: part.trim(), isSupplementary: false };
  };

  // 쉼표 구분 우선 시도
  const commaParts = diagnosis.split(/[,，、]/).map(s => s.trim()).filter(Boolean);
  if (commaParts.length > 1) return commaParts.map(parseOnePart);

  // 쉼표 없이 ICD 코드가 공백으로 이어진 경우 (예: "J06.9 급성 상기도 감염 Z87.39 ...")
  const spaceSplitParts = diagnosis.split(/\s+(?=[A-Z]\d{2}(?:\.\d+)?(?:\s|$))/).map(s => s.trim()).filter(Boolean);
  if (spaceSplitParts.length > 1) return spaceSplitParts.map(parseOnePart);

  return [parseOnePart(diagnosis.trim())];
}

function DiagnosisDisplay({ diagnosis }: { diagnosis: string }) {
  if (!diagnosis) {
    return <span className="italic" style={{ color: "var(--color-text-muted)" }}>인식이 되지 않았어요. 직접 입력해주세요</span>;
  }

  const entries = parseDiagnosis(diagnosis);
  const mainEntries = entries.filter(e => !e.isSupplementary);
  const suppEntries = entries.filter(e => e.isSupplementary);

  const parts: string[] = [
    ...mainEntries.map(e => e.label),
    ...suppEntries.map(e => `(${e.code ? `${e.code} ` : ""}${e.label})`),
  ];
  return <span className="font-medium">{parts.join(", ")}</span>;
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
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [processing, setProcessing] = useState(true);
  const [ocrFailed, setOcrFailed] = useState(false);
  const [alertMessage, setAlertMessage] = useState<string | null>(null);

  const pollOcrStatus = useCallback(async () => {
    const res = await api.getPrescription(prescriptionId);
    if (!res.success || !res.data) return;
    const pData = res.data as { ocr_status: string };
    if (pData.ocr_status === "ocr_failed") {
      setProcessing(false);
      setOcrFailed(true);
    } else if (pData.ocr_status === "ocr_completed" || pData.ocr_status === "guide_completed" || pData.ocr_status === "confirmed") {
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
    const saveRes = await api.updateOcr(prescriptionId, data);
    setSaving(false);
    if (saveRes.success) {
      setEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } else {
      setAlertMessage("저장에 실패했습니다. 다시 시도해주세요.");
    }
  };

  const handleGenerate = async () => {
    if (!data) return;

    const missingFields: string[] = [];
    if (!data.hospital_name) missingFields.push("병원명");
    if (!data.doctor_name) missingFields.push("담당의");
    if (!data.prescription_date) missingFields.push("처방일");
    if (!data.diagnosis) missingFields.push("진단명");
    data.medications.forEach((med, i) => {
      const label = `${i + 1}번 약물`;
      if (!med.name) missingFields.push(`${label} 약품명`);
      if (!med.dosage) missingFields.push(`${label} 용량`);
      if (!med.frequency) missingFields.push(`${label} 복용 방법`);
      if (!med.duration) missingFields.push(`${label} 복용기간`);
    });

    if (missingFields.length > 0) {
      setAlertMessage(`${missingFields.join(", ")} 정보를 빠짐없이 입력해야 넘어갈 수 있습니다.`);
      return;
    }

    setGenerating(true);
    const res = await api.createGuide(prescriptionId);
    if (res.success && res.data) {
      const guideData = res.data as { id: number };
      router.push(`/guides/${guideData.id}`);
    } else {
      setGenerating(false);
      setAlertMessage(res.error || "가이드 생성에 실패했습니다. 처방전 내용을 확인해주세요.");
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
      <div className="fixed inset-0 flex flex-col z-50" style={{ background: 'var(--color-bg)' }}>
        <div className="flex-1 w-full relative">
          <img
            src={loadingImg}
            alt="알쓸신약 로딩"
            className="absolute inset-0 w-full h-full object-contain p-4"
          />
        </div>

        <div className="pb-16 pt-8 text-center backdrop-blur-md z-10 shadow-[0_-20px_25px_-5px_rgba(255,255,255,0.8)]" style={{ background: 'rgba(255,255,255,0.8)', borderTop: '1px solid var(--color-border)' }}>
          <p className="text-xl font-semibold" style={{ color: 'var(--color-text)' }}>OCR로 처방전을 분석하고 있습니다...</p>
          <p className="mt-2" style={{ color: 'var(--color-text-muted)' }}>지루하지 않게 잠시만 사진을 감상하며 기다려주세요</p>
        </div>
      </div>
    );
  }

  if (ocrFailed) {
    return (
      <AppLayout>
        <div className="flex flex-col items-center justify-center py-20 text-center gap-6">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: 'var(--color-danger-soft)' }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="var(--color-danger)"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
          </div>
          <p className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>이미지 분석에 실패했습니다</p>
          <p style={{ color: 'var(--color-text-muted)' }}>처방전이 선명하게 찍혔는지 확인 후 다시 시도해 주세요.</p>
          <button
            onClick={() => router.push("/prescriptions/upload")}
            className="px-8 py-3 rounded-lg text-white text-base font-semibold"
            style={{ background: 'var(--color-primary)' }}
          >
            다시 업로드하기
          </button>
        </div>
      </AppLayout>
    );
  }

  if (!data) {
    return <AppLayout><p style={{ color: 'var(--color-text-muted)' }}>로딩 중...</p></AppLayout>;
  }

  return (
    <AppLayout>
      {/* 누락 필드 알림 모달 */}
      {alertMessage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <div className="rounded-2xl p-8 mx-6 w-full max-w-sm shadow-2xl" style={{ background: 'var(--color-bg)' }}>
            <p className="text-xl font-bold mb-2" style={{ color: 'var(--color-text)' }}>입력 누락 안내</p>
            <p className="text-lg mt-3 mb-8 leading-relaxed" style={{ color: 'var(--color-text)' }}>{alertMessage}</p>
            <button
              onClick={() => setAlertMessage(null)}
              className="w-full py-3 rounded-xl text-lg font-semibold text-white"
              style={{ background: 'var(--color-primary)' }}
            >
              확인
            </button>
          </div>
        </div>
      )}
      {saveSuccess && (
        <div className="mb-4 px-4 py-3 rounded-lg text-sm font-medium alert-success">
          저장이 완료되었습니다.
        </div>
      )}
      <h1 className="text-2xl font-bold mb-2">처방전 내용 확인</h1>
      <p className="mb-4" style={{ color: 'var(--color-text-muted)' }}>처방전이 성공적으로 인식되었습니다. 내용을 확인하고 필요시 수정해주세요.</p>

      {/* Stepper */}
      <div className="flex items-center gap-2 mb-8">
        <div className="px-4 py-2 rounded-full text-sm" style={{ background: 'var(--color-surface)', color: 'var(--color-text-muted)' }}>처방전 올리기</div>
        <span style={{ color: 'var(--color-text-muted)' }}>→</span>
        <div className="px-4 py-2 rounded-full text-sm font-medium text-white" style={{ background: 'var(--color-primary)' }}>내용 확인</div>
        <span style={{ color: 'var(--color-text-muted)' }}>→</span>
        <div className="px-4 py-2 rounded-full text-sm" style={{ background: 'var(--color-surface)', color: 'var(--color-text-muted)' }}>가이드 생성</div>
      </div>

      {/* Basic info */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-bold">기본 정보</h2>
          {!editing && (
            <button onClick={() => setEditing(true)} className="px-5 py-2 rounded-lg text-base font-semibold text-white transition-opacity hover:opacity-80" style={{ background: 'var(--color-primary)' }}>수정하기</button>
          )}
        </div>
        <div className="rounded-2xl p-6 grid grid-cols-2 gap-4" style={{ background: 'var(--color-surface)' }}>
          <div>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>병원명</p>
            {editing ? (
              <input value={data.hospital_name || ""} onChange={(e) => setData({ ...data, hospital_name: e.target.value })} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="px-3 py-2 w-full text-base input-field" />
            ) : (
              <p className="font-medium">{data.hospital_name || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
            )}
          </div>
          <div>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>담당의</p>
            {editing ? (
              <input value={data.doctor_name || ""} onChange={(e) => setData({ ...data, doctor_name: e.target.value })} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="px-3 py-2 w-full text-base input-field" />
            ) : (
              <p className="font-medium">{data.doctor_name || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
            )}
          </div>
          <div>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>처방일</p>
            {editing ? (
              <input type="date" value={data.prescription_date || ""} onChange={(e) => setData({ ...data, prescription_date: e.target.value })} className="px-3 py-2 w-full text-base input-field" />
            ) : (
              <p className="font-medium">{data.prescription_date || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
            )}
          </div>
          <div>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>진단명</p>
            {editing ? (
              <input value={data.diagnosis || ""} onChange={(e) => setData({ ...data, diagnosis: e.target.value })} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="px-3 py-2 w-full text-base input-field" />
            ) : (
              <div className="font-medium"><DiagnosisDisplay diagnosis={data.diagnosis || ""} /></div>
            )}
          </div>
        </div>
        <p className="text-base font-semibold mt-3" style={{ color: 'var(--color-text-muted)' }}>인식된 처방전 내용이 맞는지 반드시 확인해주세요. 맞지 않는 부분이 있으면 수정 버튼을 눌러 수정해주세요</p>
      </section>

      {/* Medications */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">처방 약물</h2>
        <div className="rounded-2xl p-5 space-y-4" style={{ background: 'var(--color-surface)' }}>
          {data.medications.map((med, i) => (
            <div key={i} className="app-card p-5 relative">
              {editing && (
                <button onClick={() => removeMed(i)} className="absolute top-3 right-3 text-xs px-2 py-1 rounded-lg transition-colors" style={{ color: 'var(--color-text-muted)' }}>
                  제거
                </button>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>약품명</p>
                  {editing ? (
                    <input value={med.name} onChange={(e) => updateMed(i, "name", e.target.value)} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="px-3 py-2 w-full text-base input-field" />
                  ) : (
                    <p className="font-medium">{med.name || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
                  )}
                </div>
                <div>
                  <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>용량</p>
                  {editing ? (
                    <input value={med.dosage} onChange={(e) => updateMed(i, "dosage", e.target.value)} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="px-3 py-2 w-full text-base input-field" />
                  ) : (
                    <p>{med.dosage || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
                  )}
                </div>
                <div>
                  <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>복용 방법</p>
                  {editing ? (
                    <input value={med.frequency} onChange={(e) => updateMed(i, "frequency", e.target.value)} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="px-3 py-2 w-full text-base input-field" />
                  ) : (
                    <p>{med.frequency || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
                  )}
                </div>
                <div>
                  <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>복용기간</p>
                  {editing ? (
                    <input value={med.duration || ""} onChange={(e) => updateMed(i, "duration", e.target.value)} placeholder="인식이 되지 않았어요. 직접 입력해주세요" className="px-3 py-2 w-full text-base input-field" />
                  ) : (
                    <p>{med.duration || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>인식이 되지 않았어요. 직접 입력해주세요</span>}</p>
                  )}
                </div>
                <div className="col-span-2">
                  <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>복용 지시사항</p>
                  {editing ? (
                    <input value={med.instructions || ""} onChange={(e) => updateMed(i, "instructions", e.target.value)} placeholder="추가 지시 사항이 없다면 비워두셔도 됩니다. (※ 가장 정확한 복약 방법은 의사 및 약사의 안내를 우선해 주세요.)" className="px-3 py-2 w-full text-base input-field" />
                  ) : (
                    <p>{med.instructions || <span className="italic" style={{ color: 'var(--color-text-muted)' }}>추가 지시 사항이 없다면 비워두셔도 됩니다. (※ 가장 정확한 복약 방법은 의사 및 약사의 안내를 우선해 주세요.)</span>}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 면책 문구 */}
      <p className="text-xs text-center mb-4 leading-relaxed" style={{ color: 'var(--color-text-muted)' }}>
        본 서비스는 글자 인식 기술을 활용하여 입력을 돕는 보조 도구입니다.<br />
        정확한 정보 입력 및 복약에 대한 최종 확인은 사용자 본인에게 있습니다.
      </p>

      {/* Buttons */}
      <div className="flex gap-4">
        <button onClick={() => router.push("/prescriptions/upload")} className="flex-1 py-3 rounded-lg btn-outline">
          이전 단계로
        </button>
        {editing ? (
          <button onClick={handleSave} disabled={saving} className="flex-1 py-3 rounded-lg btn-primary disabled:opacity-50">
            {saving ? "저장 중..." : "수정"}
          </button>
        ) : null}
        <button
          onClick={handleGenerate}
          disabled={generating || editing}
          className="flex-1 py-3 btn-primary"
        >
          {generating ? "생성 중..." : "가이드 생성 →"}
        </button>
      </div>
    </AppLayout>
  );
}
