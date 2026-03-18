"use client";

import { useAuthGuard } from "@/hooks/useAuthGuard";
import Header from "./Header";
import ProxyBanner from "./ProxyBanner";
import Sidebar from "./Sidebar";
import BottomNav from "./BottomNav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { loading, authorized } = useAuthGuard();

  if (loading || !authorized) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-bg)' }}>
        <p style={{ color: 'var(--color-text-muted)' }}>로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--color-bg)' }}>
      <ProxyBanner />
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-4 md:p-6 pb-24 md:pb-6">{children}</main>
      </div>
      <BottomNav />
    </div>
  );
}
