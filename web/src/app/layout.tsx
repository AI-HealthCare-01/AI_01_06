import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { KakaoRegistrationProvider } from "@/lib/kakao-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "& Sullivan - AI 복약 가이드",
  description: "처방전 기반 맞춤형 AI 복약 가이드 서비스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={`${geistSans.variable} antialiased`}>
        <KakaoRegistrationProvider>
          <AuthProvider>{children}</AuthProvider>
        </KakaoRegistrationProvider>
      </body>
    </html>
  );
}
