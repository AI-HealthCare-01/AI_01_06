"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

interface MedicationDetail {
  id: number;
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions: string;
}

export default function MedicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [med, setMed] = useState<MedicationDetail | null>(null);

  useEffect(() => {
    api.getMedication(Number(params.id)).then((res) => {
      if (res.success && res.data) setMed(res.data as MedicationDetail);
    });
  }, [params.id]);

  if (!med) return <AppLayout><p className="text-gray-500">로딩 중...</p></AppLayout>;

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-6">약품 상세</h1>
      <div className="bg-gray-100 rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div><p className="text-sm text-gray-500">약물명</p><p className="font-bold text-lg">{med.name}</p></div>
          <div><p className="text-sm text-gray-500">용량</p><p>{med.dosage}</p></div>
          <div><p className="text-sm text-gray-500">복용 방법</p><p>{med.frequency}</p></div>
          <div><p className="text-sm text-gray-500">투여 기간</p><p>{med.duration}</p></div>
          <div className="col-span-2"><p className="text-sm text-gray-500">복용 지침</p><p>{med.instructions}</p></div>
        </div>
      </div>
      <button onClick={() => router.back()} className="mt-6 border px-6 py-2 rounded-lg">이전</button>
    </AppLayout>
  );
}
