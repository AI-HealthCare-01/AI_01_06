"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const POLL_INTERVAL_MS = 5_000;

interface Person {
  mapping_id: number;
  id: number;
  nickname: string;
  name: string;
}

async function handleShare(inviteUrl: string) {
  const shareData = {
    title: "AI Health - 보호자 연결 초대",
    text: "보호자 연결을 위한 초대 링크입니다.",
    url: inviteUrl,
  };

  if (typeof navigator.share === "function" && navigator.canShare?.(shareData)) {
    try {
      await navigator.share(shareData);
      return;
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
    }
  }

  try {
    await navigator.clipboard.writeText(inviteUrl);
    alert("초대 링크가 클립보드에 복사되었습니다.");
  } catch {
    prompt("아래 링크를 복사하세요:", inviteUrl);
  }
}

function IconRefresh({ spinning }: { spinning: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ transition: "transform 0.4s", transform: spinning ? "rotate(360deg)" : "rotate(0deg)" }}
    >
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  );
}

export default function CaregiversPage() {
  const { user } = useAuth();
  const role = user?.role ?? "";
  const isGuardian = role === "GUARDIAN";

  const pageTitle = isGuardian ? "돌봄 대상 관리" : "나의 보호자";
  const listLabel = isGuardian ? "돌봄 대상 목록" : "보호자 목록";
  const emptyLabel = isGuardian ? "연결된 돌봄 대상이 없습니다." : "연결된 보호자가 없습니다.";
  const inviteDescription = isGuardian
    ? "돌봄 대상에게 초대 링크를 전송하여 연결을 요청하세요."
    : "보호자에게 초대 링크를 전송하여 연결을 요청하세요.";

  const [people, setPeople] = useState<Person[]>([]);
  const [loadError, setLoadError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [inviteUrl, setInviteUrl] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState("");
  const [revokeError, setRevokeError] = useState("");

  // 목록 fetch (silent: true이면 로딩 인디케이터 없이 폴링용으로 사용)
  const fetchPeople = useCallback(
    (silent = false) => {
      if (!silent) setRefreshing(true);
      setLoadError("");
      const req = isGuardian ? api.listPatients() : role === "PATIENT" ? api.listMyCaregivers() : null;
      if (!req) {
        setRefreshing(false);
        return Promise.resolve();
      }
      return req.then((res) => {
        if (res.success && res.data) setPeople(res.data);
        else if (!silent) setLoadError(res.error || "목록을 불러오지 못했습니다.");
      }).finally(() => {
        if (!silent) setRefreshing(false);
      });
    },
    [role, isGuardian]
  );

  // 초기 로드
  useEffect(() => {
    if (!role) return;
    void fetchPeople();
  }, [role, fetchPeople]);

  // 폴링 — 탭이 보일 때만 5초마다 자동 갱신
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startPolling = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = setInterval(() => {
      if (document.visibilityState === "visible") void fetchPeople(true);
    }, POLL_INTERVAL_MS);
  }, [fetchPeople]);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!role) return;
    startPolling();
    const onVisibility = () => (document.visibilityState === "visible" ? startPolling() : stopPolling());
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [role, startPolling, stopPolling]);

  const handleManualRefresh = () => {
    void fetchPeople();
  };

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

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-6">{pageTitle}</h1>

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
              style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}
            >
              {inviteUrl}
            </div>
            <div className="flex gap-2">
              <button onClick={() => handleShare(inviteUrl)} className="flex-1 py-2 btn-primary text-sm">
                공유하기
              </button>
              <button
                onClick={() => setInviteUrl("")}
                className="py-2 px-4 rounded-lg text-sm font-medium"
                style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", color: "var(--color-text-muted)" }}
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
            <button onClick={handleCreateInvite} disabled={inviting} className="btn-primary py-2 px-6 text-sm">
              {inviting ? "생성 중..." : "초대 링크 만들기"}
            </button>
          </div>
        )}
      </section>

      {/* 연결 목록 섹션 */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold" style={{ color: "var(--color-text)" }}>
            {listLabel}
          </h2>
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            aria-label="목록 새로고침"
            className="p-1.5 rounded-lg"
            style={{ color: "var(--color-text-muted)" }}
            onMouseEnter={(e) => { e.currentTarget.style.background = "var(--color-surface)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = ""; }}
          >
            <IconRefresh spinning={refreshing} />
          </button>
        </div>

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
            {emptyLabel}
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
                    @{person.nickname} · {isGuardian ? "돌봄 대상" : "보호자"}
                  </p>
                </div>
                <button
                  onClick={() => handleRevoke(person.mapping_id, person.name)}
                  className="text-sm px-3 py-1.5 rounded-lg font-medium"
                  style={{ background: "var(--color-surface)", border: "1px solid var(--color-danger)", color: "var(--color-danger)" }}
                >
                  연결 해제
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </AppLayout>
  );
}
