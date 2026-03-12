"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import Header from "@/components/Header";
import { api, setRefreshToken, setToken } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useSocialRegistration, type SocialRegistrationData } from "@/lib/social-registration-context";

const INITIAL_FORM = {
  email: "", nickname: "", password: "", passwordConfirm: "",
  name: "", birth_date: "", gender: "", phone: "",
};

const INITIAL_AGREEMENTS = { terms: false, privacy: false, marketing: false };

export default function SignupPage() {
  const [step, setStep] = useState<"role" | "form">("role");
  const [role, setRole] = useState<"patient" | "caregiver">("patient");
  const [form, setForm] = useState({ ...INITIAL_FORM });
  const [agreements, setAgreements] = useState({ ...INITIAL_AGREEMENTS });
  const [socialData, setSocialData] = useState<SocialRegistrationData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, refreshUser } = useAuth();
  const { socialRegistration, setSocialRegistration } = useSocialRegistration();

  // source=kakao 또는 source=google 인 경우 소셜 플로우 감지
  const source = searchParams.get("source");
  const isSocialFlow = source === "kakao" || source === "google";

  // B1/B2: source 파라미터 변화 감지 — 소셜 플로우 이탈 시 상태 전체 초기화
  // Next.js 16 App Router: 같은 경로에서 쿼리만 변경 시 컴포넌트 리마운트 없음
  // didMountRef: 초기 마운트 실행 방지 (React 19 Strict Mode 2회 실행 대응)
  const didMountRef = useRef(false);
  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }
    if (!source) {
      setSocialData(null);
      setSocialRegistration(null);
      setStep("role");
      setForm({ ...INITIAL_FORM });
      setAgreements({ ...INITIAL_AGREEMENTS });
      setError("");
    }
  }, [source, setSocialRegistration]);

  // 소셜 모드 감지: Context(인메모리)에서 등록 데이터 읽기
  // !socialData 가드: 이미 읽은 경우 재실행 방지
  useEffect(() => {
    if (isSocialFlow && socialRegistration && !socialData) {
      setSocialData(socialRegistration);
      setSocialRegistration(null);
      setForm((f) => ({
        ...f,
        email: socialRegistration.email,
        nickname: socialRegistration.nickname,
        // Google은 name 제공 → 자동 채우기, Kakao는 undefined → 유지
        ...(socialRegistration.name ? { name: socialRegistration.name } : {}),
      }));
    }
  }, [isSocialFlow, socialRegistration, setSocialRegistration, socialData]);

  const updateForm = (key: string, value: string) => setForm((prev) => ({ ...prev, [key]: value }));

  const handleKakaoSignup = async () => {
    const res = await api.getKakaoUrl();
    if (res.success && res.data) {
      window.location.href = res.data.url;
    } else {
      setError("카카오 로그인을 시작할 수 없습니다.");
    }
  };

  const handleGoogleSignup = async () => {
    const res = await api.getGoogleUrl();
    if (res.success && res.data) {
      window.location.href = res.data.url;
    } else {
      setError("Google 로그인을 시작할 수 없습니다.");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!socialData && form.password !== form.passwordConfirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }
    if (!agreements.terms || !agreements.privacy) {
      setError("필수 약관에 동의해주세요.");
      return;
    }

    setLoading(true);
    setError("");
    const roleValue = role === "patient" ? "PATIENT" : "GUARDIAN";

    if (socialData?.provider === "KAKAO" || socialData?.provider === "GOOGLE") {
      // 소셜 회원가입 플로우 (Kakao / Google 공통)
      const register =
        socialData.provider === "GOOGLE" ? api.googleRegister : api.kakaoRegister;
      const providerLabel = socialData.provider === "GOOGLE" ? "Google" : "카카오";

      const res = await register({
        registration_token: socialData.token,
        email: form.email,
        name: form.name,
        nickname: form.nickname,
        role: roleValue,
        birth_date: form.birth_date || null,
        gender: form.gender || null,
        phone: form.phone || null,
        terms_of_service: agreements.terms,
        privacy_policy: agreements.privacy,
        marketing_consent: agreements.marketing,
      });
      if (!res.success || !res.data) {
        setError(res.error || `${providerLabel} 가입에 실패했습니다.`);
        setLoading(false);
        return;
      }
      setToken(res.data.access_token);
      setRefreshToken(res.data.refresh_token);
      await refreshUser();
      router.push(roleValue === "PATIENT" ? "/onboarding" : "/dashboard");
      return;
    }

    // LOCAL 회원가입 플로우 (기존 변경 없음)
    const res = await api.signup({
      email: form.email,
      nickname: form.nickname,
      password: form.password,
      name: form.name,
      birth_date: form.birth_date || null,
      gender: form.gender || null,
      phone: form.phone || null,
      role: roleValue,
      terms_of_service: agreements.terms,
      privacy_policy: agreements.privacy,
      marketing_consent: agreements.marketing,
    });
    if (!res.success) {
      setError(res.error || "회원가입에 실패했습니다.");
      setLoading(false);
      return;
    }
    const loginError = await login(form.email, form.password);
    if (loginError) {
      setError(loginError);
      setLoading(false);
      return;
    }
    router.push(roleValue === "PATIENT" ? "/onboarding" : "/dashboard");
  };

  if (step === "role") {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="bg-white p-8 rounded-lg shadow-sm w-full max-w-md space-y-6 text-center">
            <h1 className="text-2xl font-bold">회원가입</h1>
            <p className="text-gray-800">계정 유형을 선택해주세요</p>
            <div className="space-y-4">
              <button
                onClick={() => { setRole("patient"); setStep("form"); }}
                className="w-full border-2 border-blue-600 text-blue-600 py-4 rounded-lg hover:bg-blue-50 font-medium"
              >
                일반 (환자)
              </button>
              <button
                onClick={() => { setRole("caregiver"); setStep("form"); }}
                className="w-full border-2 border-green-600 text-green-600 py-4 rounded-lg hover:bg-green-50 font-medium"
              >
                보호자
              </button>
            </div>
            {/* 소셜 버튼: OAuth 인증 후 재진입 시 숨김 (#6 요구사항) */}
            {!isSocialFlow && (
              <>
                <div className="relative mt-2">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="bg-white px-2 text-gray-400">소셜 계정으로 간편 가입</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleKakaoSignup}
                  className="w-full flex items-center justify-center gap-2 bg-[#FEE500] text-[#191919] py-4 rounded-lg hover:bg-[#F6DC00] font-medium"
                >
                  카카오로 시작하기
                </button>
                <button
                  type="button"
                  onClick={handleGoogleSignup}
                  className="w-full flex items-center justify-center gap-2 bg-white border border-gray-300 text-gray-700 py-4 rounded-lg hover:bg-gray-50 font-medium"
                >
                  <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                    <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                    <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
                  </svg>
                  Google로 시작하기
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex items-center justify-center py-10">
        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-sm w-full max-w-lg space-y-4">
          <h1 className="text-2xl font-bold">회원가입</h1>
          <p className="text-sm text-gray-700">
            계정 유형 : {role === "patient" ? "일반" : "보호자"}
            {socialData?.provider === "KAKAO" && (
              <span className="ml-2 text-yellow-600 font-medium">· 카카오 연동</span>
            )}
            {socialData?.provider === "GOOGLE" && (
              <span className="ml-2 text-blue-600 font-medium">· Google 연동</span>
            )}
          </p>
          {error && <p className="text-red-500 text-sm">{error}</p>}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                이메일
                {socialData?.provider === "KAKAO" && socialData.email && (
                  <span className="text-xs text-gray-400 ml-1">(카카오 계정)</span>
                )}
                {socialData?.provider === "GOOGLE" && (
                  <span className="text-xs text-gray-400 ml-1">(Google 계정)</span>
                )}
              </label>
              <input
                type="email" required value={form.email}
                onChange={(e) => updateForm("email", e.target.value)}
                placeholder={socialData?.provider === "KAKAO" && !socialData.email ? "이메일을 입력해주세요" : ""}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">별명</label>
              <input
                type="text" required value={form.nickname}
                onChange={(e) => updateForm("nickname", e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
              {socialData && (
                <p className="text-xs text-gray-400 mt-1">자동 입력됨, 변경 가능</p>
              )}
            </div>
          </div>

          {/* 비밀번호: LOCAL 전용 */}
          {!socialData && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">비밀번호</label>
                <input
                  type="password" required value={form.password}
                  onChange={(e) => updateForm("password", e.target.value)}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">비밀번호 확인</label>
                <input
                  type="password" required value={form.passwordConfirm}
                  onChange={(e) => updateForm("passwordConfirm", e.target.value)}
                  className="w-full border rounded px-3 py-2"
                />
                {form.passwordConfirm && form.password !== form.passwordConfirm && (
                  <p className="text-xs text-red-500 mt-1">비밀번호가 일치하지 않습니다</p>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">이름</label>
              <input
                type="text" required value={form.name}
                onChange={(e) => updateForm("name", e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
              {socialData?.provider === "GOOGLE" && socialData.name && (
                <p className="text-xs text-gray-400 mt-1">Google 이름 자동 입력, 변경 가능</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">생년월일</label>
              <input
                type="date" value={form.birth_date}
                onChange={(e) => updateForm("birth_date", e.target.value)}
                className="w-full border rounded px-3 py-2"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">성별</label>
            <select
              value={form.gender}
              onChange={(e) => updateForm("gender", e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">선택</option>
              <option value="M">남성</option>
              <option value="F">여성</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">핸드폰 번호</label>
            <input
              type="tel" value={form.phone}
              onChange={(e) => updateForm("phone", e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <hr />
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox" checked={agreements.terms}
                onChange={(e) => setAgreements((a) => ({ ...a, terms: e.target.checked }))}
              />
              <span className="text-sm">이용약관에 동의합니다 (필수)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox" checked={agreements.privacy}
                onChange={(e) => setAgreements((a) => ({ ...a, privacy: e.target.checked }))}
              />
              <span className="text-sm">개인정보 처리방침에 동의합니다 (필수)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox" checked={agreements.marketing}
                onChange={(e) => setAgreements((a) => ({ ...a, marketing: e.target.checked }))}
              />
              <span className="text-sm">마케팅 정보 수신에 동의합니다 (선택)</span>
            </label>
          </div>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => { setStep("role"); setSocialData(null); }}
              className="flex-1 border py-2 rounded-lg"
            >
              이전
            </button>
            <button
              type="submit" disabled={loading}
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "가입 중..." : "회원가입"}
            </button>
          </div>
          {!socialData && (
            <p className="text-center text-sm text-gray-500">
              이미 계정이 있으신가요?{" "}
              <Link href="/login" className="text-blue-600 hover:underline">로그인</Link>
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
