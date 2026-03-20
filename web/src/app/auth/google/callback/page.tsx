"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, setRefreshToken, setToken } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useSocialRegistration } from "@/lib/social-registration-context";

function GoogleCallbackContent() {
  const [error, setError] = useState("");
  const searchParams = useSearchParams();
  const router = useRouter();
  const { refreshUser } = useAuth();
  const { setSocialRegistration } = useSocialRegistration();

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const errorParam = searchParams.get("error");

    // 사용자 Google 인증 취소 또는 에러
    if (errorParam) {
      router.replace("/login");
      return;
    }
    if (!code || !state) {
      setError("잘못된 접근입니다.");
      return;
    }

    (async () => {
      const res = await api.googleCallback(code, state);
      if (!res.success || !res.data) {
        const errorMsg = res.error || "Google 로그인에 실패했습니다.";
        router.replace(`/signup?social_error=${encodeURIComponent(errorMsg)}`);
        return;
      }

      if (res.data.status === "login") {
        setToken(res.data.access_token!);
        setRefreshToken(res.data.refresh_token!);
        const user = await refreshUser();
        router.replace(user?.role === "GUARDIAN" ? "/caregivers" : "/dashboard");
      } else if (res.data.status === "new_user") {
        // in-memory Context 저장 (sessionStorage 회피 → XSS 방지)
        setSocialRegistration({
          provider: "GOOGLE",
          token: res.data.registration_token!,
          email: res.data.google_profile?.email ?? "",
          nickname: res.data.google_profile?.nickname ?? "",
          name: res.data.google_profile?.name ?? "",
        });
        router.replace("/signup?source=google");
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
      <p style={{ color: "var(--color-text-muted)" }}>Google 인증 처리 중...</p>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--color-bg)" }}>
          <p style={{ color: "var(--color-text-muted)" }}>Google 인증 처리 중...</p>
        </div>
      }
    >
      <GoogleCallbackContent />
    </Suspense>
  );
}
