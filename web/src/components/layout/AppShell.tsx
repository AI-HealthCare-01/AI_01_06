import AppHeader from './AppHeader';
import type React from "react";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />
      <main>{children}</main>
    </div>
  );
}
