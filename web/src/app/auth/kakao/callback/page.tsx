"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, setRefreshToken, setToken } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useSocialRegistration } from "@/lib/social-registration-context";

function KakaoCallbackContent() {
  const [error, setError] = useState("");
  const searchParams = useSearchParams();
  const router = useRouter();
  const { refreshUser } = useAuth();
  const { setSocialRegistration } = useSocialRegistration();

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const errorParam = searchParams.get("error");

    // 사용자 카카오 인증 취소
    if (errorParam === "access_denied") {
      router.replace("/login");
      return;
    }
    if (!code || !state) {
      setError("잘못된 접근입니다.");
      return;
    }

    (async () => {
      const res = await api.kakaoCallback(code, state);
      if (!res.success || !res.data) {
        const errorCode = res.error?.includes("삭제") ? "deleted_email"
          : res.error?.includes("이메일") ? "email_conflict" : "kakao_fail";
        router.replace(`/signup?social_error=${errorCode}`);
        return;
      }

      if (res.data.status === "login") {
        setToken(res.data.access_token!);
        setRefreshToken(res.data.refresh_token!);
        const user = await refreshUser();
        router.replace(user?.role === "GUARDIAN" ? "/caregivers" : "/dashboard");
      } else if (res.data.status === "new_user") {
        // in-memory Context 저장 (sessionStorage XSS 방지)
        setSocialRegistration({
          provider: "KAKAO",
          token: res.data.registration_token!,
          email: res.data.kakao_profile!.email,
          nickname: res.data.kakao_profile!.nickname,
          // name: undefined — Kakao는 비즈앱 없이 실명 미제공
        });
        router.replace("/signup?source=kakao");
      }
    })();
  }, [searchParams, router, refreshUser, setSocialRegistration]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--color-bg)" }}>
        <div className="p-8 rounded-lg text-center space-y-4" style={{ background: "var(--color-card-bg)", boxShadow: "0 1px 3px rgba(45,42,38,0.06)" }}>
          <p style={{ color: "var(--color-danger)" }}>{error}</p>
          <button
            onClick={() => router.push("/login")}
            className="hover:underline"
            style={{ color: "var(--color-primary)" }}
          >
            로그인으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--color-bg)" }}>
      <p style={{ color: "var(--color-text-muted)" }}>카카오 인증 처리 중...</p>
    </div>
  );
}

export default function KakaoCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--color-bg)" }}>
          <p style={{ color: "var(--color-text-muted)" }}>카카오 인증 처리 중...</p>
        </div>
      }
    >
      <KakaoCallbackContent />
    </Suspense>
  );
}
