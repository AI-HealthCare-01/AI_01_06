"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const menuItems = [
  { href: "/dashboard", label: "대시보드", roles: ["patient", "caregiver"] },
  { href: "/prescriptions/upload", label: "처방전 업로드", roles: ["patient"] },
  { href: "/guides", label: "가이드 내역", roles: ["patient", "caregiver"] },
  { href: "/chat", label: "AI 상담", roles: ["patient", "caregiver"] },
  { href: "/settings", label: "설정", roles: ["patient", "caregiver"] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const role = user?.role || "patient";

  return (
    <aside className="w-60 bg-white border-r border-gray-200 min-h-screen p-4">
      <nav className="space-y-1">
        {menuItems
          .filter((item) => item.roles.includes(role))
          .map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-4 py-3 rounded-lg text-sm font-medium ${
                pathname.startsWith(item.href)
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {item.label}
            </Link>
          ))}
      </nav>
    </aside>
  );
}
