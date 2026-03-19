"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface MedicationGuide {
  name: string;
  dosage: string;
  frequency: string;
  timing?: string;
  duration?: string;
  instructions: string;
  effect: string;
  precautions: string;
}

interface GuideContent {
  medication_guides: MedicationGuide[];
  warnings: {
    drug_interactions: string;
    side_effects: string;
    alcohol: string;
  };
  lifestyle: {
    diet: string[];
    exercise: string[];
  };
  disclaimer: string;
}

interface GuideData {
  id: number;
  prescription_id: number;
  status: string;
  prescription_info: {
    hospital_name: string;
    doctor_name: string;
    prescription_date: string;
    diagnosis: string;
  };
  content: GuideContent | null;
  created_at: string;
}

export default function GuideDetailPage() {
  const params = useParams();
  const router = useRouter();
  const guideId = Number(params.id);
  const [guide, setGuide] = useState<GuideData | null>(null);
  const [generating, setGenerating] = useState(true);
  const [regenerating, setRegenerating] = useState(false);

  const handleRegenerate = async () => {
    if (!guide || !confirm("가이드를 재생성하면 기존 가이드가 삭제됩니다. 계속할까요?")) return;
    setRegenerating(true);
    const res = await api.createGuide(guide.prescription_id, true);
    setRegenerating(false);
    if (res.success && res.data) {
      const newGuide = res.data as { id: number };
      router.push(`/guides/${newGuide.id}`);
    }
  };

  const pollGuide = useCallback(async () => {
    const res = await api.getGuide(guideId);
    if (!res.success || !res.data) return;
    const data = res.data as GuideData;
    setGuide(data);
    if (data.status === "completed" || data.status === "failed") {
      setGenerating(false);
    }
  }, [guideId]);

  useEffect(() => {
    pollGuide();
    const interval = setInterval(() => {
      if (generating) pollGuide();
    }, 2000);
    return () => clearInterval(interval);
  }, [pollGuide, generating]);

  if (generating && (!guide || !guide.content)) {
    return (
      <AppLayout>
        <h1 className="text-2xl font-bold mb-2">AI 복약 가이드 생성 중</h1>
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mb-4" style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }} />
          <p style={{ color: 'var(--color-text-muted)' }}>AI가 맞춤형 복약 가이드를 생성하고 있습니다...</p>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>잠시만 기다려주세요</p>
        </div>
      </AppLayout>
    );
  }

  if (guide?.status === "failed") {
    return (
      <AppLayout>
        <h1 className="text-2xl font-bold mb-2">가이드 생성 실패</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700 font-medium">가이드 생성 중 오류가 발생했습니다.</p>
          <p className="text-red-500 text-sm mt-1">처방전 내용을 확인하고 다시 시도해주세요.</p>
        </div>
        <div className="flex gap-4 mt-4">
          <Link href="/guides" className="flex-1 py-3 rounded-lg text-center btn-outline">
            가이드 목록으로
          </Link>
          <Link href={`/prescriptions/${guide.prescription_id}/ocr?from=guide&guideId=${guide.id}`} className="flex-1 py-3 rounded-lg text-center btn-primary">
            처방전 다시 확인하기
          </Link>
        </div>
      </AppLayout>
    );
  }

  if (!guide || !guide.content) {
    return <AppLayout><p style={{ color: 'var(--color-text-muted)' }}>로딩 중...</p></AppLayout>;
  }

  const { content, prescription_info } = guide;

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-2">AI 복약 가이드</h1>
      <p className="mb-1" style={{ color: 'var(--color-text-muted)' }}>맞춤형 복약 지침과 건강 관리 가이드</p>

      <div className="alert-success rounded-lg p-4 mb-6">
        <p className="text-sm">
          가이드 생성 완료 - 처방전을 기반으로 맞춤형 복약 가이드가 생성되었습니다.
        </p>
        <p className="text-xs mt-1" style={{ color: 'var(--color-success)' }}>생성일: {guide.created_at.slice(0, 10)}</p>
      </div>

      {/* Prescription info */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">처방 정보</h2>
        <div className="rounded-lg p-4 grid grid-cols-2 gap-3" style={{ background: 'var(--color-surface)' }}>
          <div><p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>병원명</p><p className="font-medium">{prescription_info.hospital_name}</p></div>
          <div><p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>담당의</p><p className="font-medium">{prescription_info.doctor_name || "정보 없음"}</p></div>
          <div><p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>처방일</p><p className="font-medium">{prescription_info.prescription_date}</p></div>
          <div><p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>진단명</p><p className="font-medium">{prescription_info.diagnosis}</p></div>
        </div>
      </section>

      {/* Medication guides */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">복약 정보</h2>
        <div className="space-y-4">
          {content.medication_guides.map((med, i) => (
            <div key={i} className="rounded-lg p-4" style={{ background: 'var(--color-card-bg)', border: '1px solid var(--color-border)' }}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-lg">{med.name} {med.dosage}</h3>
                <span className="text-xs px-3 py-1 rounded-full" style={{ background: 'var(--color-primary-soft)', color: 'var(--color-primary)' }}>{med.effect}</span>
              </div>
              <div className="space-y-1 text-sm">
                {med.timing && <p><span style={{ color: 'var(--color-text-muted)' }}>복용 시간대 :</span> {med.timing}</p>}
                <p><span style={{ color: 'var(--color-text-muted)' }}>복용 횟수 :</span> {med.frequency}</p>
                {med.duration && <p><span style={{ color: 'var(--color-text-muted)' }}>복용 기간 :</span> {med.duration}</p>}
                <p><span style={{ color: 'var(--color-text-muted)' }}>복용 방법 :</span> {med.instructions}</p>
                <p className="px-2 py-1 rounded mt-2" style={{ background: 'var(--color-warning-soft)', color: 'var(--color-warning-text)' }}>
                  <span className="font-medium">주의 사항 :</span> {med.precautions}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Warnings */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">중요 주의사항</h2>
        <div className="rounded-lg p-4 space-y-3 text-sm" style={{ background: 'var(--color-card-bg)', border: '1px solid var(--color-border)' }}>
          <div>
            <p className="font-bold">약물 상호작용 :</p>
            <p className="ml-4" style={{ color: 'var(--color-text-muted)' }}>{content.warnings.drug_interactions}</p>
          </div>
          <div>
            <p className="font-bold">부작용 발생 시 :</p>
            <p className="ml-4" style={{ color: 'var(--color-text-muted)' }}>{content.warnings.side_effects}</p>
          </div>
          <div>
            <p className="font-bold">음주 :</p>
            <p className="ml-4" style={{ color: 'var(--color-text-muted)' }}>{content.warnings.alcohol}</p>
          </div>
        </div>
      </section>

      {/* Lifestyle */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">생활 습관 권장사항</h2>
        <div className="rounded-lg p-4 space-y-3 text-sm" style={{ background: 'var(--color-card-bg)', border: '1px solid var(--color-border)' }}>
          <div>
            <p className="font-bold">식이 관리</p>
            <ul className="list-disc list-inside ml-2" style={{ color: 'var(--color-text-muted)' }}>
              {content.lifestyle.diet.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </div>
          <div>
            <p className="font-bold">운동</p>
            <ul className="list-disc list-inside ml-2" style={{ color: 'var(--color-text-muted)' }}>
              {content.lifestyle.exercise.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <div className="alert-danger rounded-lg p-4 mb-6 text-sm">
        {content.disclaimer}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Link href="/guides" className="flex-1 py-3 rounded-lg text-center btn-outline">
          가이드 목록으로
        </Link>
        <Link href={`/prescriptions/${guide.prescription_id}/ocr?from=guide&guideId=${guide.id}`} className="flex-1 py-3 rounded-lg text-center btn-outline">
          처방전 재확인
        </Link>
        <Link href={`/chat?prescriptionId=${guide.prescription_id}`} className="flex-1 py-3 rounded-lg text-center btn-primary">
          AI에게 질문하기
        </Link>
      </div>
      <div className="mt-3">
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="w-full py-3 rounded-lg text-center btn-outline disabled:opacity-50"
        >
          {regenerating ? "재생성 중..." : "프로필 반영하여 재생성"}
        </button>
      </div>
    </AppLayout>
  );
}
