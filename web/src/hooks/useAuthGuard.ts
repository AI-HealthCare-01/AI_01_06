"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const PATIENT_ONLY_PREFIXES = [
  "/dashboard",
  "/prescriptions",
  "/guides",
  "/medications",
  "/onboarding",
];

export function useAuthGuard() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;

    if (!user) {
      router.replace(`/login?returnUrl=${encodeURIComponent(pathname)}`);
      return;
    }

    if (user.role === "GUARDIAN") {
      const isPatientOnly = PATIENT_ONLY_PREFIXES.some((prefix) => pathname.startsWith(prefix));
      if (isPatientOnly) {
        router.replace("/caregivers");
      }
    }
  }, [user, loading, router, pathname]);

  const isPatientOnly = PATIENT_ONLY_PREFIXES.some((prefix) => pathname.startsWith(prefix));
  const roleBlocked = !!user && user.role === "GUARDIAN" && isPatientOnly;

  return { user, loading, authorized: !loading && !!user && !roleBlocked };
}
