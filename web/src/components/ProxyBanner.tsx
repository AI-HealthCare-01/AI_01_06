"use client";

import { usePatient } from "@/lib/patient-context";
import { useRouter } from "next/navigation";

export default function ProxyBanner() {
  const { activePatient, clearPatient, isProxyMode } = usePatient();
  const router = useRouter();

  if (!isProxyMode || !activePatient) return null;

  const handleExit = () => {
    clearPatient();
    router.replace("/caregivers");
  };

  return (
    <div
      className="sticky top-0 z-[51] w-full px-4 py-2 flex items-center justify-between text-sm"
      style={{
        backgroundColor: "var(--color-primary-soft)",
        color: "var(--color-primary)",
        borderBottom: "1px solid var(--color-primary)",
      }}
    >
      <span>
        <strong>{activePatient.name}</strong>님의 건강 정보를 확인하고 있습니다
      </span>
      <button
        onClick={handleExit}
        className="px-3 py-1 rounded-lg text-xs font-medium"
        style={{ backgroundColor: "var(--color-primary)", color: "#fff" }}
      >
        돌아가기
      </button>
    </div>
  );
}
