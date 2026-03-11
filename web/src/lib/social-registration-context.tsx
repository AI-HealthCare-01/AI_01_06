"use client";

import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

export interface SocialRegistrationData {
  provider: "KAKAO" | "GOOGLE";
  token: string;
  email: string;
  nickname: string;
  name?: string; // Google만 제공 (Kakao는 비즈앱 없이 실명 불가)
}

interface SocialRegistrationContextType {
  socialRegistration: SocialRegistrationData | null;
  setSocialRegistration: (data: SocialRegistrationData | null) => void;
}

const SocialRegistrationContext =
  createContext<SocialRegistrationContextType | null>(null);

export function SocialRegistrationProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [socialRegistration, setSocialRegistration] =
    useState<SocialRegistrationData | null>(null);

  return (
    <SocialRegistrationContext.Provider
      value={{ socialRegistration, setSocialRegistration }}
    >
      {children}
    </SocialRegistrationContext.Provider>
  );
}

export function useSocialRegistration(): SocialRegistrationContextType {
  const ctx = useContext(SocialRegistrationContext);
  if (!ctx)
    throw new Error(
      "useSocialRegistration must be used within SocialRegistrationProvider"
    );
  return ctx;
}
