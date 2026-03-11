"use client";

// Kakao 전용 import 경로 호환 레이어
// 실제 구현은 social-registration-context.tsx 로 통합됨
export {
  SocialRegistrationProvider as KakaoRegistrationProvider,
  useSocialRegistration as useKakaoRegistration,
} from "@/lib/social-registration-context";

export type {
  SocialRegistrationData as KakaoRegistrationData,
} from "@/lib/social-registration-context";
