"use client";

import { useCallback, useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface Person {
  id: number;
  nickname: string;
  name: string;
}

const ROLE_LABEL: Record<string, string> = {
  PATIENT: "환자",
  GUARDIAN: "보호자",
};

async function handleShare(inviteUrl: string) {
  const shareData = {
    title: "AI Health - 보호자 연결 초대",
    text: "보호자 연결을 위한 초대 링크입니다.",
    url: inviteUrl,
  };

  // Web Share API — Firefox 미지원, Chrome/Safari/Edge 지원
  if (typeof navigator.share === "function" && navigator.canShare?.(shareData)) {
    try {
      await navigator.share(shareData);
      return;
    } catch (err) {
      // 사용자가 공유 취소 시 AbortError → 무시
      if (err instanceof DOMException && err.name === "AbortError") return;
    }
  }

  // Fallback: Clipboard API (HTTPS 필수, localhost 제외)
  try {
    await navigator.clipboard.writeText(inviteUrl);
    alert("초대 링크가 클립보드에 복사되었습니다.");
  } catch {
    // 최후 fallback: prompt (HTTP 환경 등)
    prompt("아래 링크를 복사하세요:", inviteUrl);
  }
}

export default function CaregiversPage() {
  const { user } = useAuth();
  const role = user?.role ?? "";

  const [people, setPeople] = useState<Person[]>([]);
  const [loadError, setLoadError] = useState("");
  const [inviteUrl, setInviteUrl] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState("");
  const [revokeError, setRevokeError] = useState("");

  const fetchPeople = useCallback(() => {
    setLoadError("");
    return (role === "GUARDIAN" ? api.listPatients() : api.listMyCaregivers()).then((res) => {
      if (res.success && res.data) setPeople(res.data);
      else setLoadError(res.error || "목록을 불러오지 못했습니다.");
    });
  }, [role]);

  useEffect(() => {
    if (!role) return;
    fetchPeople();
  }, [role, fetchPeople]);

  const handleCreateInvite = async () => {
    setInviting(true);
    setInviteError("");
    const res = await api.createInvite();
    if (res.success && res.data) {
      setInviteUrl(res.data.invite_url);
    } else {
      setInviteError(res.error || "초대 링크 생성에 실패했습니다.");
    }
    setInviting(false);
  };

  const handleRevoke = async (mappingId: number, personName: string) => {
    if (!confirm(`${personName}님과의 연결을 해제하시겠습니까?`)) return;
    setRevokeError("");
    const res = await api.revokeMapping(mappingId);
    if (res.success) {
      await fetchPeople();
    } else {
      setRevokeError(res.error || "연결 해제에 실패했습니다.");
    }
  };

  const isGuardian = role === "GUARDIAN";
  const listLabel = isGuardian ? "관리 중인 환자" : "내 보호자";
  const inviteDescription = isGuardian
    ? "환자에게 초대 링크를 전송하여 연결을 요청하세요."
    : "보호자에게 초대 링크를 전송하여 연결을 요청하세요.";
  const roleLabel = ROLE_LABEL[role] ?? role;

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-6">보호자 관리</h1>

      {/* 초대 링크 생성 섹션 */}
      <section
        className="p-4 md:p-6 rounded-lg mb-6"
        style={{ background: "var(--color-card-bg)", border: "1px solid var(--color-border)" }}
      >
        <h2 className="text-base font-semibold mb-1" style={{ color: "var(--color-text)" }}>
          초대 링크 생성
        </h2>
        <p className="text-sm mb-4" style={{ color: "var(--color-text-muted)" }}>
          {inviteDescription}
        </p>

        {inviteUrl ? (
          <div className="space-y-3">
            <div
              className="p-3 rounded-lg text-sm break-all"
              style={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                color: "var(--color-text)",
              }}
            >
              {inviteUrl}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleShare(inviteUrl)}
                className="flex-1 py-2 btn-primary text-sm"
              >
                공유하기
              </button>
              <button
                onClick={() => { setInviteUrl(""); }}
                className="py-2 px-4 rounded-lg text-sm font-medium"
                style={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  color: "var(--color-text-muted)",
                }}
              >
                닫기
              </button>
            </div>
            <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
              링크는 48시간 후 만료됩니다. 수락 후에는 재사용할 수 없습니다.
            </p>
          </div>
        ) : (
          <div>
            {inviteError && (
              <p className="text-sm mb-2" style={{ color: "var(--color-danger)" }}>
                {inviteError}
              </p>
            )}
            <button
              onClick={handleCreateInvite}
              disabled={inviting}
              className="btn-primary py-2 px-6 text-sm"
            >
              {inviting ? "생성 중..." : "초대 링크 만들기"}
            </button>
          </div>
        )}
      </section>

      {/* 연결 목록 섹션 */}
      <section>
        <h2 className="text-base font-semibold mb-3" style={{ color: "var(--color-text)" }}>
          {listLabel}
        </h2>

        {loadError && (
          <p className="text-sm mb-3" style={{ color: "var(--color-danger)" }}>
            {loadError}
          </p>
        )}
        {revokeError && (
          <p className="text-sm mb-3" style={{ color: "var(--color-danger)" }}>
            {revokeError}
          </p>
        )}

        {people.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            연결된 {isGuardian ? "환자" : "보호자"}가 없습니다.
          </p>
        ) : (
          <ul className="space-y-2">
            {people.map((person) => (
              <li
                key={person.id}
                className="flex items-center justify-between p-4 rounded-lg"
                style={{ background: "var(--color-card-bg)", border: "1px solid var(--color-border)" }}
              >
                <div>
                  <p className="font-medium" style={{ color: "var(--color-text)" }}>
                    {person.name}
                  </p>
                  <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                    @{person.nickname} · {isGuardian ? "환자" : "보호자"}
                  </p>
                </div>
                <button
                  onClick={() => handleRevoke(person.id, person.name)}
                  className="text-sm px-3 py-1.5 rounded-lg font-medium"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-danger)",
                    color: "var(--color-danger)",
                  }}
                >
                  연결 해제
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="mt-6 text-xs" style={{ color: "var(--color-text-muted)" }}>
        현재 {roleLabel} 계정으로 로그인되어 있습니다.
      </p>
    </AppLayout>
  );
}
