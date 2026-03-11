"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, setRefreshToken, setToken } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useSocialRegistration } from "@/lib/social-registration-context";

export default function GoogleCallbackPage() {
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
        setError(res.error || "Google 로그인에 실패했습니다.");
        return;
      }

      if (res.data.status === "login") {
        setToken(res.data.access_token!);
        setRefreshToken(res.data.refresh_token!);
        await refreshUser();
        router.replace("/dashboard");
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-sm text-center space-y-4">
          <p className="text-red-500">{error}</p>
          <button
            onClick={() => router.push("/login")}
            className="text-blue-600 hover:underline"
          >
            로그인으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-500">Google 인증 처리 중...</p>
    </div>
  );
}
