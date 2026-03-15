"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface InviterInfo {
  inviter_name: string;
  inviter_nickname: string;
  inviter_role: string;
}

const ROLE_LABEL: Record<string, string> = {
  PATIENT: "환자",
  GUARDIAN: "보호자",
};

export default function InviteAcceptPage() {
  const params = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const token = typeof params.token === "string" ? params.token : "";

  const [inviter, setInviter] = useState<InviterInfo | null>(null);
  const [loadError, setLoadError] = useState("");
  const [accepting, setAccepting] = useState(false);
  const [acceptError, setAcceptError] = useState("");

  // 미로그인 시 로그인 페이지로 리다이렉트
  useEffect(() => {
    if (!authLoading && !user) {
      router.replace(`/login?returnUrl=/invite/${token}`);
    }
  }, [authLoading, user, router, token]);

  // 토큰 검증 및 초대자 정보 로드 (authLoading 중에는 호출하지 않음)
  useEffect(() => {
    if (authLoading || !user || !token) return;
    api.validateInvite(token).then((res) => {
      if (res.success && res.data) {
        setInviter(res.data);
      } else {
        setLoadError(res.error || "초대 링크가 유효하지 않습니다.");
      }
    });
  }, [authLoading, user, token]);

  const handleAccept = async () => {
    setAccepting(true);
    setAcceptError("");
    const res = await api.acceptInvite(token);
    if (res.success) {
      router.push("/caregivers");
    } else {
      setAcceptError(res.error || "수락에 실패했습니다.");
      setAccepting(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--color-bg)" }}>
        <p style={{ color: "var(--color-text-muted)" }}>로딩 중...</p>
      </div>
    );
  }

  if (!user) return null;

  const expectedRole = inviter?.inviter_role === "PATIENT" ? "GUARDIAN" : "PATIENT";
  const roleLabel = ROLE_LABEL[inviter?.inviter_role ?? ""] ?? inviter?.inviter_role;
  const expectedRoleLabel = ROLE_LABEL[expectedRole] ?? expectedRole;

  return (
    <div className="min-h-screen" style={{ background: "var(--color-bg)" }}>
      <Header />
      <div className="flex items-center justify-center py-10 px-4 pb-24 md:pb-10">
        <div
          className="p-6 md:p-8 rounded-lg w-full max-w-md space-y-6"
          style={{ background: "var(--color-card-bg)", border: "1px solid var(--color-border)" }}
        >
          <h1 className="text-2xl font-bold text-center">보호자 연결 초대</h1>

          {loadError ? (
            <div className="text-center space-y-4">
              <p style={{ color: "var(--color-danger)" }}>{loadError}</p>
              <button onClick={() => router.push("/caregivers")} className="btn-primary px-6 py-2">
                보호자 관리로 이동
              </button>
            </div>
          ) : inviter ? (
            <div className="space-y-6">
              <div
                className="p-4 rounded-lg text-center"
                style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}
              >
                <p className="text-lg font-semibold" style={{ color: "var(--color-text)" }}>
                  {inviter.inviter_name}
                  <span
                    className="ml-2 text-sm font-normal"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    ({inviter.inviter_nickname})
                  </span>
                </p>
                <p className="mt-1 text-sm" style={{ color: "var(--color-text-muted)" }}>
                  {roleLabel}님이 보호자 연결을 초대했습니다.
                </p>
                <p className="mt-2 text-sm font-medium" style={{ color: "var(--color-primary)" }}>
                  이 초대는 {expectedRoleLabel} 계정으로만 수락할 수 있습니다.
                </p>
              </div>

              {user.role !== expectedRole && (
                <div
                  className="p-3 rounded-lg text-sm text-center"
                  style={{ background: "var(--color-warning-soft, #fef3c7)", color: "var(--color-warning, #92400e)" }}
                >
                  현재 <strong>{ROLE_LABEL[user.role] ?? user.role}</strong> 계정으로 로그인되어 있습니다.
                  <br />
                  {expectedRoleLabel} 계정으로 로그인 후 이 링크를 다시 접속해 주세요.
                </div>
              )}

              {acceptError && (
                <p className="text-sm text-center" style={{ color: "var(--color-danger)" }}>
                  {acceptError}
                </p>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => router.push("/caregivers")}
                  className="flex-1 py-2 rounded-lg text-sm font-medium"
                  style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}
                >
                  취소
                </button>
                <button
                  onClick={handleAccept}
                  disabled={accepting || user.role !== expectedRole}
                  className="flex-1 py-2 btn-primary"
                >
                  {accepting ? "수락 중..." : "수락하기"}
                </button>
              </div>
            </div>
          ) : (
            <p className="text-center" style={{ color: "var(--color-text-muted)" }}>
              초대 정보를 불러오는 중...
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
