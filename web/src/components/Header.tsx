"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [fontSize, setFontSize] = useState<"normal" | "large">("normal");

  const toggleFontSize = () => {
    const next = fontSize === "normal" ? "large" : "normal";
    setFontSize(next);
    document.documentElement.style.fontSize = next === "large" ? "20px" : "16px";
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <Link href={user ? "/dashboard" : "/"} className="text-xl font-bold text-blue-600">
       Project & Sullivan
      </Link>
      <div className="flex items-center gap-4">
        <button
          onClick={toggleFontSize}
          className="text-sm text-gray-500 hover:text-gray-700 border rounded px-2 py-1"
        >
          {fontSize === "normal" ? "큰 글씨" : "작은 글씨"} 모드
        </button>
        {user ? (
          <>
            <span className="text-sm text-gray-600">{user.nickname}</span>
            <button
              onClick={() => { logout(); router.push("/"); }}
              className="text-sm text-gray-500 hover:text-red-500 bg-gray-100 px-3 py-1 rounded"
            >
              로그아웃
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="text-sm text-gray-600 hover:text-blue-600">로그인</Link>
            <Link href="/signup" className="text-sm text-white bg-blue-600 px-3 py-1 rounded hover:bg-blue-700">회원가입</Link>
          </>
        )}
      </div>
    </header>
  );
}
