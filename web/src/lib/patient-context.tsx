"use client";

import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";

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
  const [activePatient, setActivePatient] = useState<PatientInfo | null>(loadPatient);

  const selectPatient = useCallback((patient: PatientInfo) => {
    setActivePatient(patient);
    sessionStorage.setItem("activePatient", JSON.stringify(patient));
  }, []);

  const clearPatient = useCallback(() => {
    setActivePatient(null);
    sessionStorage.removeItem("activePatient");
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
