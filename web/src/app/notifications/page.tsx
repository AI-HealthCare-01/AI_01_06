"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface NotificationItem {
  id: number;
  notification_type: string;
  title: string;
  body: string | null;
  is_read: boolean;
  created_at: string;
}

const TYPE_ICON: Record<string, string> = {
  MEDICATION: "\uD83D\uDC8A",
  CAREGIVER: "\uD83D\uDEE1\uFE0F",
  SYSTEM: "\uD83D\uDCE2",
};

const TYPE_LABEL: Record<string, string> = {
  MEDICATION: "\uBCF5\uC57D",
  CAREGIVER: "\uBCF4\uD638\uC790",
  SYSTEM: "\uC2DC\uC2A4\uD15C",
};

export default function NotificationsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) { router.replace("/login"); return; }
    fetchNotifications();
  }, [user, authLoading]);

  const fetchNotifications = async () => {
    setLoading(true);
    const res = await api.listNotifications();
    if (res.success && res.data) setNotifications(res.data as NotificationItem[]);
    setLoading(false);
  };

  const handleMarkRead = async (id: number) => {
    await api.markNotificationRead(id);
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
  };

  const handleReadAll = async () => {
    await api.readAllNotifications();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  if (authLoading || !user) return null;

  return (
    <AppLayout>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-bold" style={{ color: "var(--color-text)" }}>
          알림센터
        </h1>
        {unreadCount > 0 && (
          <button
            onClick={handleReadAll}
            className="text-sm font-medium cursor-pointer"
            style={{ color: "var(--color-primary)" }}
          >
            전체 읽음
          </button>
        )}
      </div>

      {/* 알림 목록 */}
      {loading ? (
        <p style={{ color: "var(--color-text-muted)" }}>로딩 중...</p>
      ) : notifications.length === 0 ? (
        <div className="app-card p-8 text-center">
          <p style={{ color: "var(--color-text-muted)" }}>알림이 없습니다.</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {notifications.map((n) => (
            <li
              key={n.id}
              onClick={() => !n.is_read && handleMarkRead(n.id)}
              className="app-card p-4 flex items-start gap-3 transition-colors cursor-pointer"
              style={{ opacity: n.is_read ? 0.6 : 1 }}
              role="button"
              aria-label={`${n.title} ${n.is_read ? "(읽음)" : "(읽지않음)"}`}
            >
              {/* 읽지 않음 표시 */}
              {!n.is_read && (
                <span
                  className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                  style={{ backgroundColor: "var(--color-primary)" }}
                />
              )}
              {n.is_read && <span className="w-2 flex-shrink-0" />}

              {/* 타입 아이콘 */}
              <span className="text-lg flex-shrink-0" aria-hidden="true">
                {TYPE_ICON[n.notification_type] || "\uD83D\uDD14"}
              </span>

              {/* 내용 */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span
                    className="text-xs px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: "var(--color-surface)", color: "var(--color-text-muted)" }}
                  >
                    {TYPE_LABEL[n.notification_type] || n.notification_type}
                  </span>
                </div>
                <p className="text-sm font-medium mt-1" style={{ color: "var(--color-text)" }}>
                  {n.title}
                </p>
                {n.body && (
                  <p className="text-xs mt-0.5 truncate" style={{ color: "var(--color-text-muted)" }}>
                    {n.body}
                  </p>
                )}
                <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
                  {new Date(n.created_at).toLocaleString("ko-KR")}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </AppLayout>
  );
}
