"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface MedicationGuide {
  name: string;
  dosage: string;
  frequency: string;
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
  const guideId = Number(params.id);
  const [guide, setGuide] = useState<GuideData | null>(null);
  const [generating, setGenerating] = useState(true);

  const pollGuide = useCallback(async () => {
    const res = await api.getGuide(guideId);
    if (!res.success || !res.data) return;
    const data = res.data as GuideData;
    setGuide(data);
    if (data.status === "completed") {
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
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-gray-600">AI가 맞춤형 복약 가이드를 생성하고 있습니다...</p>
          <p className="text-sm text-gray-400 mt-1">잠시만 기다려주세요</p>
        </div>
      </AppLayout>
    );
  }

  if (!guide || !guide.content) {
    return <AppLayout><p className="text-gray-500">로딩 중...</p></AppLayout>;
  }

  const { content, prescription_info } = guide;

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-2">AI 복약 가이드</h1>
      <p className="text-gray-600 mb-1">맞춤형 복약 지침과 건강 관리 가이드</p>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
        <p className="text-green-800 text-sm">
          가이드 생성 완료 - 처방전을 기반으로 맞춤형 복약 가이드가 생성되었습니다.
        </p>
        <p className="text-green-600 text-xs mt-1">생성일: {guide.created_at.slice(0, 10)}</p>
      </div>

      {/* Prescription info */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">처방 정보</h2>
        <div className="bg-gray-100 rounded-lg p-4 grid grid-cols-2 gap-3">
          <div><p className="text-xs text-gray-500">병원명</p><p className="font-medium">{prescription_info.hospital_name}</p></div>
          <div><p className="text-xs text-gray-500">담당의</p><p className="font-medium">{prescription_info.doctor_name}</p></div>
          <div><p className="text-xs text-gray-500">처방일</p><p className="font-medium">{prescription_info.prescription_date}</p></div>
          <div><p className="text-xs text-gray-500">진단명</p><p className="font-medium">{prescription_info.diagnosis}</p></div>
        </div>
      </section>

      {/* Medication guides */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">복약 정보</h2>
        <div className="space-y-4">
          {content.medication_guides.map((med, i) => (
            <div key={i} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-lg">{med.name} {med.dosage}</h3>
                <span className="bg-blue-100 text-blue-700 text-xs px-3 py-1 rounded-full">{med.effect}</span>
              </div>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">복용 시간 :</span> {med.frequency}</p>
                <p><span className="text-gray-500">복용 방법 :</span> {med.instructions}</p>
                <p className="bg-yellow-50 text-yellow-800 px-2 py-1 rounded mt-2">
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
        <div className="bg-white border rounded-lg p-4 space-y-3 text-sm">
          <div>
            <p className="font-bold">약물 상호작용 :</p>
            <p className="text-gray-600 ml-4">{content.warnings.drug_interactions}</p>
          </div>
          <div>
            <p className="font-bold">부작용 발생 시 :</p>
            <p className="text-gray-600 ml-4">{content.warnings.side_effects}</p>
          </div>
          <div>
            <p className="font-bold">음주 :</p>
            <p className="text-gray-600 ml-4">{content.warnings.alcohol}</p>
          </div>
        </div>
      </section>

      {/* Lifestyle */}
      <section className="mb-6">
        <h2 className="text-lg font-bold mb-2">생활 습관 권장사항</h2>
        <div className="bg-white border rounded-lg p-4 space-y-3 text-sm">
          <div>
            <p className="font-bold">식이 관리</p>
            <ul className="list-disc list-inside text-gray-600 ml-2">
              {content.lifestyle.diet.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </div>
          <div>
            <p className="font-bold">운동</p>
            <ul className="list-disc list-inside text-gray-600 ml-2">
              {content.lifestyle.exercise.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-sm text-red-800">
        {content.disclaimer}
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <Link href="/guides" className="flex-1 border py-3 rounded-lg text-center">
          AI 가이드 기록 저장
        </Link>
        <Link href={`/chat?prescriptionId=${guide.prescription_id}`} className="flex-1 bg-blue-600 text-white py-3 rounded-lg text-center hover:bg-blue-700">
          AI에게 질문하기
        </Link>
      </div>
    </AppLayout>
  );
}
