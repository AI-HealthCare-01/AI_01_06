"use client";

import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

interface KakaoRegistrationData {
  token: string;
  email: string;
  nickname: string;
}

interface KakaoRegistrationContextType {
  kakaoRegistration: KakaoRegistrationData | null;
  setKakaoRegistration: (data: KakaoRegistrationData | null) => void;
}

const KakaoRegistrationContext =
  createContext<KakaoRegistrationContextType | null>(null);

export function KakaoRegistrationProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [kakaoRegistration, setKakaoRegistration] =
    useState<KakaoRegistrationData | null>(null);

  return (
    <KakaoRegistrationContext.Provider
      value={{ kakaoRegistration, setKakaoRegistration }}
    >
      {children}
    </KakaoRegistrationContext.Provider>
  );
}

export function useKakaoRegistration(): KakaoRegistrationContextType {
  const ctx = useContext(KakaoRegistrationContext);
  if (!ctx)
    throw new Error(
      "useKakaoRegistration must be used within KakaoRegistrationProvider"
    );
  return ctx;
}
