import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { PatientProvider } from "@/lib/patient-context";
import { SocialRegistrationProvider } from "@/lib/social-registration-context";

export const metadata: Metadata = {
  title: "Sullivan - AI 복약 가이드",
  description: "처방전 기반 맞춤형 AI 복약 가이드 서비스",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased">
        <SocialRegistrationProvider>
          <AuthProvider>
            <PatientProvider>{children}</PatientProvider>
          </AuthProvider>
        </SocialRegistrationProvider>
      </body>
    </html>
  );
}
