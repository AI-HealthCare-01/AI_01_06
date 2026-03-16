"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useAuth } from "./auth-context";

interface PatientInfo {
  id: number;
  name: string;
  nickname: string;
}

interface PatientContextType {
  activePatient: PatientInfo | null;
  selectPatient: (patient: PatientInfo) => void;
  clearPatient: () => void;
  isProxyMode: boolean;
}

const PatientContext = createContext<PatientContextType | null>(null);

function loadPatient(): PatientInfo | null {
  if (typeof window === "undefined") return null;
  try {
    const saved = sessionStorage.getItem("activePatient");
    return saved ? JSON.parse(saved) : null;
  } catch {
    sessionStorage.removeItem("activePatient");
    return null;
  }
}

export function PatientProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [activePatient, setActivePatient] = useState<PatientInfo | null>(loadPatient);

  const selectPatient = useCallback((patient: PatientInfo) => {
    setActivePatient(patient);
    sessionStorage.setItem("activePatient", JSON.stringify(patient));
  }, []);

  const clearPatient = useCallback(() => {
    setActivePatient(null);
    sessionStorage.removeItem("activePatient");
  }, []);

  // 로그아웃 시 대리 모드 해제 (React 상태 동기화)
  useEffect(() => {
    if (!user) clearPatient();
  }, [user, clearPatient]);

  // 대리 모드 중 매핑 해제 감지 (api.ts에서 proxy-revoked 이벤트 발행)
  useEffect(() => {
    const handler = () => setActivePatient(null);
    window.addEventListener("proxy-revoked", handler);
    return () => window.removeEventListener("proxy-revoked", handler);
  }, []);

  return (
    <PatientContext.Provider value={{ activePatient, selectPatient, clearPatient, isProxyMode: activePatient !== null }}>
      {children}
    </PatientContext.Provider>
  );
}

export function usePatient() {
  const ctx = useContext(PatientContext);
  if (!ctx) throw new Error("usePatient must be used within PatientProvider");
  return ctx;
}
