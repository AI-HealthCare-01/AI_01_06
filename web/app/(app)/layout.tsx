import type React from "react";
import AppShell from '../../src/components/layout/AppShell';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
