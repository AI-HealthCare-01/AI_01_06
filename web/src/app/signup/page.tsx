"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import Header from "@/components/Header";
import { api, setRefreshToken, setToken } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useSocialRegistration, type SocialRegistrationData } from "@/lib/social-registration-context";
import {
  validateEmail,
  validateNickname,
  validatePassword,
  validatePasswordConfirm,
  validateName,
  validateBirthDate,
  validateGender,
  validatePhonePrefix,
  validatePhoneMiddle,
  validatePhoneLast,
  validateAllFields,
  getPasswordStrength,
  type FieldErrorKey,
  type PhoneState,
} from "@/lib/signup-validation";

const sanitizeNickname = (value: string): string =>
  value.trim().replace(/[^가-힣a-zA-Z0-9]/g, "");

const INITIAL_FORM = {
  email: "", nickname: "", password: "", passwordConfirm: "",
  name: "", birth_date: "", gender: "",
};

const INITIAL_PHONE: PhoneState = {
  prefix: "010",
  prefixCustom: "",
  middle: "",
  last: "",
};

const INITIAL_AGREEMENTS = { terms: false, privacy: false, marketing: false };

const PHONE_PREFIXES = ["010", "011", "016", "017", "018", "019", "직접입력"];

const TODAY = new Date().toISOString().split("T")[0];
const MIN_DATE = (() => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 100);
  return d.toISOString().split("T")[0];
})();

function SignupContent() {
  const [step, setStep] = useState<"role" | "form">("role");
  const [role, setRole] = useState<"patient" | "caregiver">("patient");
  const [form, setForm] = useState({ ...INITIAL_FORM });
  const [phoneState, setPhoneState] = useState<PhoneState>({ ...INITIAL_PHONE });
  const [agreements, setAgreements] = useState({ ...INITIAL_AGREEMENTS });
  const [socialData, setSocialData] = useState<SocialRegistrationData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldErrorKey, string>>>({});
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, refreshUser } = useAuth();
  const { socialRegistration, setSocialRegistration } = useSocialRegistration();

  const prefixSelectRef = useRef<HTMLSelectElement>(null);
  const prefixCustomRef = useRef<HTMLInputElement>(null);
  const middleRef = useRef<HTMLInputElement>(null);
  const lastRef = useRef<HTMLInputElement>(null);
  const skipBlurRef = useRef(false);

  // source=kakao 또는 source=google 인 경우 소셜 플로우 감지
  const source = searchParams.get("source");
  const isSocialFlow = source === "kakao" || source === "google";

  // B1/B2: source 파라미터 변화 감지 — 소셜 플로우 이탈 시 상태 전체 초기화
  // Next.js 16 App Router: 같은 경로에서 쿼리만 변경 시 컴포넌트 리마운트 없음
  // prevSourceRef: 이전 source 값 추적 (React 19 Strict Mode double-mount 안전)
  const prevSourceRef = useRef(source);
  useEffect(() => {
    const prevSource = prevSourceRef.current;
    prevSourceRef.current = source;
    // source가 실제로 있다가 null로 변한 경우만 초기화 (마운트 시 오발동 방지)
    if (prevSource !== null && source === null) {
      setSocialData(null);
      setSocialRegistration(null);
      setStep("role");
      setForm({ ...INITIAL_FORM });
      setPhoneState({ ...INITIAL_PHONE });
      setAgreements({ ...INITIAL_AGREEMENTS });
      setFieldErrors({});
    }
  }, [source, setSocialRegistration, setSocialData]);

  // 콜백 에러 시 social_error 코드로 인라인 에러 표시 (allowlist — 피싱 방지)
  const SOCIAL_ERROR_MESSAGES: Record<string, string> = {
    kakao_fail: "카카오 로그인에 실패했습니다.",
    google_fail: "Google 로그인에 실패했습니다.",
    deleted_account: "삭제 대기중인 계정입니다.",
    deleted_email: "삭제 대기중인 이메일 주소입니다.",
    email_conflict: "이미 가입된 이메일주소입니다.",
  };
  useEffect(() => {
    const errorCode = searchParams.get("social_error");
    if (errorCode && SOCIAL_ERROR_MESSAGES[errorCode]) {
      setError(SOCIAL_ERROR_MESSAGES[errorCode]);
    }
  }, [searchParams]);

  // 소셜 모드 감지: Context(인메모리)에서 등록 데이터 읽기
  // !socialData 가드: 이미 읽은 경우 재실행 방지
  useEffect(() => {
    if (isSocialFlow && socialRegistration && !socialData) {
      setSocialData(socialRegistration);
      setSocialRegistration(null);
      setForm((f) => ({
        ...f,
        email: socialRegistration.email,
        nickname: sanitizeNickname(socialRegistration.nickname),
        // Google은 name 제공 → 자동 채우기, Kakao는 undefined → 유지
        ...(socialRegistration.name ? { name: socialRegistration.name } : {}),
      }));
    }
  }, [isSocialFlow, socialRegistration, setSocialRegistration, socialData]);

  // --- Validation helpers ---

  const setFieldError = (key: FieldErrorKey, msg: string | null) =>
    setFieldErrors((prev) => {
      if (msg === null) {
        const next = { ...prev };
        delete next[key];
        return next;
      }
      return { ...prev, [key]: msg };
    });

  const updateForm = (key: keyof typeof INITIAL_FORM, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    // Re-validate only if this field already has an error (교정 즉시 에러 제거)
    if (fieldErrors[key as FieldErrorKey] !== undefined) {
      const validateMap: Partial<Record<keyof typeof INITIAL_FORM, () => string | null>> = {
        email: () => validateEmail(value),
        nickname: () => validateNickname(value),
        password: () => validatePassword(value),
        passwordConfirm: () => validatePasswordConfirm(form.password, value),
        name: () => validateName(value),
        birth_date: () => validateBirthDate(value),
        gender: () => validateGender(value),
      };
      const fn = validateMap[key];
      if (fn) setFieldError(key as FieldErrorKey, fn());
    }
    // 비밀번호 변경 시 비밀번호 확인 에러도 갱신
    if (key === "password" && fieldErrors.passwordConfirm !== undefined) {
      setFieldError("passwordConfirm", validatePasswordConfirm(value, form.passwordConfirm));
    }
  };

  const handleBlur = (key: FieldErrorKey, validate: () => string | null) => {
    setFieldError(key, validate());
  };

  // --- Phone handlers ---

  const handlePhoneChange = (field: "prefixCustom" | "middle" | "last", rawValue: string) => {
    const digits = rawValue.replace(/\D/g, "");
    setPhoneState((prev) => ({ ...prev, [field]: digits }));

    const errorKey: FieldErrorKey =
      field === "prefixCustom" ? "phonePrefix" : field === "middle" ? "phoneMiddle" : "phoneLast";

    if (fieldErrors[errorKey] !== undefined) {
      if (field === "prefixCustom") {
        setFieldError(errorKey, validatePhonePrefix(phoneState.prefix, digits));
      } else {
        // 중간/끝자리: 입력 중(maxLength 미달)이면 에러 클리어, 완성 시만 검증
        if (digits.length < 4) {
          setFieldError(errorKey, null);
        } else {
          const validate = field === "middle" ? validatePhoneMiddle : validatePhoneLast;
          setFieldError(errorKey, validate(digits));
        }
      }
    }

    // 자동 포커스: 완성 시 에러 클리어 + 다음 필드로 이동
    // skipBlurRef: 자동 포커스로 인한 onBlur에서 stale state 검증 방지 (onBlur에서 리셋)
    if (field === "prefixCustom" && digits.length >= 3) {
      skipBlurRef.current = true;
      middleRef.current?.focus();
    }
    if (field === "middle" && digits.length === 4) {
      setFieldError("phoneMiddle", null);
      skipBlurRef.current = true;
      lastRef.current?.focus();
    }
  };

  const handlePhonePrefixChange = (value: string) => {
    setPhoneState((prev) => ({ ...prev, prefix: value, prefixCustom: "" }));
    if (fieldErrors.phonePrefix !== undefined) {
      setFieldError("phonePrefix", value === "직접입력" ? "앞자리 번호를 입력해주세요." : null);
    }
    if (value === "직접입력") {
      setTimeout(() => prefixCustomRef.current?.focus(), 0);
    } else {
      setTimeout(() => middleRef.current?.focus(), 0);
    }
  };

  const handlePhoneKeyDown = (
    field: "middle" | "last",
    e: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (e.key === "Backspace") {
      const currentValue = field === "middle" ? phoneState.middle : phoneState.last;
      if (currentValue === "") {
        if (field === "last") middleRef.current?.focus();
        if (field === "middle") {
          phoneState.prefix === "직접입력"
            ? prefixCustomRef.current?.focus()
            : prefixSelectRef.current?.focus();
        }
      }
    }
  };

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

    const errors = validateAllFields({ form, phoneState, socialData, agreements });
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    setError("");
    const roleValue = role === "patient" ? "PATIENT" : "GUARDIAN";

    const resolvedPrefix =
      phoneState.prefix === "직접입력" ? phoneState.prefixCustom : phoneState.prefix;
    const phone = `${resolvedPrefix}-${phoneState.middle}-${phoneState.last}`;

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
        phone: phone || null,
        terms_of_service: agreements.terms,
        privacy_policy: agreements.privacy,
        marketing_consent: agreements.marketing,
      });
      if (!res.success || !res.data) {
        setError(res.error || `${providerLabel} 가입에 실패했습니다. 다시 시도해주세요.`);
        setLoading(false);
        return;
      }
      setToken(res.data.access_token);
      setRefreshToken(res.data.refresh_token);
      await refreshUser();
      router.push(roleValue === "PATIENT" ? "/onboarding" : "/caregivers");
      return;
    }

    // LOCAL 회원가입 플로우
    const res = await api.signup({
      email: form.email,
      nickname: form.nickname,
      password: form.password,
      name: form.name,
      birth_date: form.birth_date || null,
      gender: form.gender || null,
      phone: phone || null,
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
    const loginResult = await login(form.email, form.password);
    if (typeof loginResult === "string") {
      setError(loginResult);
      setLoading(false);
      return;
    }
    router.push(loginResult.role === "PATIENT" ? "/onboarding" : "/caregivers");
  };

  const passwordStrength = form.password ? getPasswordStrength(form.password) : null;

  if (step === "role") {
    return (
      <div className="min-h-screen" style={{ background: 'var(--color-bg)' }}>
        <Header />
        <div className="flex items-center justify-center py-10 md:py-20 px-4 pb-24 md:pb-10">
          <div className="p-8 md:p-10 rounded-2xl w-full max-w-md space-y-6 text-center" style={{ background: 'var(--color-card-bg)', boxShadow: 'var(--shadow-lg)' }}>
            <h1 className="text-2xl md:text-3xl font-semibold">회원가입</h1>
            {error && <p className="text-sm" style={{ color: 'var(--color-danger)' }}>{error}</p>}
            <p style={{ color: 'var(--color-text)' }}>계정 유형을 선택해주세요</p>
            <div className="space-y-4">
              <button
                onClick={() => { setRole("patient"); setStep("form"); }}
                className="w-full border-2 py-4 rounded-xl text-base font-semibold transition-colors"
                style={{ borderColor: 'var(--color-primary)', color: 'var(--color-primary)' }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--color-primary-soft)'}
                onMouseLeave={(e) => e.currentTarget.style.background = ''}
              >
                일반 (환자)
              </button>
              <button
                onClick={() => { setRole("caregiver"); setStep("form"); }}
                className="w-full border-2 py-4 rounded-xl text-base font-semibold transition-colors"
                style={{ borderColor: 'var(--color-success)', color: 'var(--color-success)' }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--color-success-soft)'}
                onMouseLeave={(e) => e.currentTarget.style.background = ''}
              >
                보호자
              </button>
            </div>
            {/* 소셜 버튼: OAuth 인증 후 재진입 시 숨김 */}
            {!isSocialFlow && (
              <>
                <div className="relative mt-2">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t" style={{ borderColor: 'var(--color-border)' }} />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2" style={{ background: 'var(--color-card-bg)', color: 'var(--color-text-muted)' }}>소셜 계정으로 간편 가입</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleKakaoSignup}
                  className="w-full flex items-center justify-center gap-2 py-4 rounded-xl text-base font-medium hover:brightness-95 transition"
                  style={{ background: 'var(--color-kakao)', color: 'var(--color-kakao-text)' }}
                >
                  카카오로 시작하기
                </button>
                <button
                  type="button"
                  onClick={handleGoogleSignup}
                  className="w-full flex items-center justify-center gap-2 py-4 rounded-xl text-base font-medium transition"
                  style={{ background: 'var(--color-card-bg)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
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
    <div className="min-h-screen" style={{ background: 'var(--color-bg)' }}>
      <Header />
      <div className="flex items-center justify-center py-10 px-4 pb-24 md:pb-10">
        <form onSubmit={handleSubmit} className="p-8 md:p-10 rounded-2xl w-full max-w-lg space-y-4" style={{ background: 'var(--color-card-bg)', boxShadow: 'var(--shadow-lg)' }}>
          <h1 className="text-2xl md:text-3xl font-semibold">회원가입</h1>
          <p className="text-sm" style={{ color: 'var(--color-text)' }}>
            계정 유형 : {role === "patient" ? "일반" : "보호자"}
            {socialData?.provider === "KAKAO" && (
              <span className="ml-2 font-medium" style={{ color: 'var(--color-warning)' }}>· 카카오 연동</span>
            )}
            {socialData?.provider === "GOOGLE" && (
              <span className="ml-2 font-medium" style={{ color: 'var(--color-primary)' }}>· Google 연동</span>
            )}
          </p>
          {error && <p className="text-sm" style={{ color: 'var(--color-danger)' }}>{error}</p>}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                이메일
                {socialData?.provider === "KAKAO" && socialData.email && (
                  <span className="text-xs ml-1" style={{ color: 'var(--color-text-muted)' }}>(카카오 계정)</span>
                )}
                {socialData?.provider === "GOOGLE" && (
                  <span className="text-xs ml-1" style={{ color: 'var(--color-text-muted)' }}>(Google 계정)</span>
                )}
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => updateForm("email", e.target.value)}
                onBlur={() => handleBlur("email", () => validateEmail(form.email))}
                placeholder={socialData?.provider === "KAKAO" && !socialData.email ? "이메일을 입력해주세요" : ""}
                className="w-full px-3 py-2 input-field"
                style={fieldErrors.email ? { borderColor: 'var(--color-danger)' } : undefined}
              />
              {fieldErrors.email && <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.email}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">별명</label>
              <input
                type="text"
                value={form.nickname}
                onChange={(e) => updateForm("nickname", e.target.value)}
                onBlur={() => handleBlur("nickname", () => validateNickname(form.nickname))}
                className="w-full px-3 py-2 input-field"
                style={fieldErrors.nickname ? { borderColor: 'var(--color-danger)' } : undefined}
              />
              {socialData && <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>자동 입력됨, 변경 가능</p>}
              {fieldErrors.nickname && <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.nickname}</p>}
            </div>
          </div>

          {/* 비밀번호: LOCAL 전용 */}
          {!socialData && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">비밀번호</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => updateForm("password", e.target.value)}
                  onBlur={() => handleBlur("password", () => validatePassword(form.password))}
                  className="w-full px-3 py-2 input-field"
                  style={fieldErrors.password ? { borderColor: 'var(--color-danger)' } : undefined}
                />
                {passwordStrength && (
                  <div className="flex gap-1 mt-1">
                    {(["weak", "fair", "strong"] as const).map((level, i) => {
                      const filled = ["weak", "fair", "strong"].indexOf(passwordStrength) >= i;
                      const bgColor =
                        passwordStrength === "strong"
                          ? "var(--color-success)"
                          : passwordStrength === "fair"
                            ? "var(--color-warning)"
                            : "var(--color-danger)";
                      return (
                        <div
                          key={level}
                          className="h-1 flex-1 rounded"
                          style={{ background: filled ? bgColor : 'var(--color-surface-alt)' }}
                        />
                      );
                    })}
                  </div>
                )}
                {fieldErrors.password && (
                  <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.password}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">비밀번호 확인</label>
                <input
                  type="password"
                  value={form.passwordConfirm}
                  onChange={(e) => updateForm("passwordConfirm", e.target.value)}
                  onBlur={() =>
                    handleBlur("passwordConfirm", () =>
                      validatePasswordConfirm(form.password, form.passwordConfirm),
                    )
                  }
                  className="w-full px-3 py-2 input-field"
                  style={fieldErrors.passwordConfirm ? { borderColor: 'var(--color-danger)' } : undefined}
                />
                {fieldErrors.passwordConfirm && (
                  <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.passwordConfirm}</p>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">이름</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => updateForm("name", e.target.value)}
                onBlur={() => handleBlur("name", () => validateName(form.name))}
                className="w-full px-3 py-2 input-field"
                style={fieldErrors.name ? { borderColor: 'var(--color-danger)' } : undefined}
              />
              {socialData?.provider === "GOOGLE" && socialData.name && (
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>Google 이름 자동 입력, 변경 가능</p>
              )}
              {fieldErrors.name && <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.name}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">생년월일</label>
              <input
                type="date"
                value={form.birth_date}
                max={TODAY}
                min={MIN_DATE}
                onChange={(e) => updateForm("birth_date", e.target.value)}
                onBlur={() => handleBlur("birth_date", () => validateBirthDate(form.birth_date))}
                className="w-full px-3 py-2 input-field"
                style={fieldErrors.birth_date ? { borderColor: 'var(--color-danger)' } : undefined}
              />
              {fieldErrors.birth_date && (
                <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.birth_date}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">성별</label>
            <select
              value={form.gender}
              onChange={(e) => updateForm("gender", e.target.value)}
              onBlur={() => handleBlur("gender", () => validateGender(form.gender))}
              className="w-full px-3 py-2 input-field"
              style={fieldErrors.gender ? { borderColor: 'var(--color-danger)' } : undefined}
            >
              <option value="">선택</option>
              <option value="M">남성</option>
              <option value="F">여성</option>
            </select>
            {fieldErrors.gender && <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.gender}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">핸드폰 번호</label>
            <div className="flex gap-2 items-center">
              <select
                ref={prefixSelectRef}
                value={phoneState.prefix}
                onChange={(e) => handlePhonePrefixChange(e.target.value)}
                className="px-2 py-2 input-field"
                style={fieldErrors.phonePrefix ? { borderColor: 'var(--color-danger)' } : undefined}
              >
                {PHONE_PREFIXES.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              {phoneState.prefix === "직접입력" && (
                <input
                  ref={prefixCustomRef}
                  type="text"
                  value={phoneState.prefixCustom}
                  onChange={(e) => handlePhoneChange("prefixCustom", e.target.value)}
                  onBlur={() => {
                    if (skipBlurRef.current) { skipBlurRef.current = false; return; }
                    handleBlur("phonePrefix", () =>
                      validatePhonePrefix(phoneState.prefix, phoneState.prefixCustom),
                    );
                  }}
                  placeholder="앞자리"
                  maxLength={4}
                  className="w-20 px-2 py-2 text-center input-field"
                  style={fieldErrors.phonePrefix ? { borderColor: 'var(--color-danger)' } : undefined}
                />
              )}
              <span style={{ color: 'var(--color-text-muted)' }}>-</span>
              <input
                ref={middleRef}
                type="text"
                value={phoneState.middle}
                onChange={(e) => handlePhoneChange("middle", e.target.value)}
                onKeyDown={(e) => handlePhoneKeyDown("middle", e)}
                onBlur={() => {
                  if (skipBlurRef.current) { skipBlurRef.current = false; return; }
                  handleBlur("phoneMiddle", () => validatePhoneMiddle(phoneState.middle));
                }}
                placeholder="0000"
                maxLength={4}
                className="w-20 px-2 py-2 text-center input-field"
                style={fieldErrors.phoneMiddle ? { borderColor: 'var(--color-danger)' } : undefined}
              />
              <span style={{ color: 'var(--color-text-muted)' }}>-</span>
              <input
                ref={lastRef}
                type="text"
                value={phoneState.last}
                onChange={(e) => handlePhoneChange("last", e.target.value)}
                onKeyDown={(e) => handlePhoneKeyDown("last", e)}
                onBlur={() => {
                  if (skipBlurRef.current) { skipBlurRef.current = false; return; }
                  handleBlur("phoneLast", () => validatePhoneLast(phoneState.last));
                }}
                placeholder="0000"
                maxLength={4}
                className="w-20 px-2 py-2 text-center input-field"
                style={fieldErrors.phoneLast ? { borderColor: 'var(--color-danger)' } : undefined}
              />
            </div>
            {fieldErrors.phonePrefix && (
              <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.phonePrefix}</p>
            )}
            {fieldErrors.phoneMiddle && (
              <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.phoneMiddle}</p>
            )}
            {fieldErrors.phoneLast && (
              <p className="text-xs mt-1" style={{ color: 'var(--color-danger)' }}>{fieldErrors.phoneLast}</p>
            )}
          </div>

          <hr />
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={agreements.terms}
                onChange={(e) => setAgreements((a) => ({ ...a, terms: e.target.checked }))}
              />
              <span className="text-sm">이용약관에 동의합니다 (필수)</span>
            </label>
            {fieldErrors.terms && (
              <p className="text-xs ml-6" style={{ color: 'var(--color-danger)' }}>{fieldErrors.terms}</p>
            )}
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={agreements.privacy}
                onChange={(e) => setAgreements((a) => ({ ...a, privacy: e.target.checked }))}
              />
              <span className="text-sm">개인정보 처리방침에 동의합니다 (필수)</span>
            </label>
            {fieldErrors.privacy && (
              <p className="text-xs ml-6" style={{ color: 'var(--color-danger)' }}>{fieldErrors.privacy}</p>
            )}
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={agreements.marketing}
                onChange={(e) => setAgreements((a) => ({ ...a, marketing: e.target.checked }))}
              />
              <span className="text-sm">마케팅 정보 수신에 동의합니다 (선택)</span>
            </label>
          </div>

          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setStep("role")}
              className="flex-1 py-2 rounded-lg btn-outline"
            >
              이전
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 rounded-lg btn-primary"
            >
              {loading ? "가입 중..." : "회원가입"}
            </button>
          </div>
          {!socialData && (
            <p className="text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
              이미 계정이 있으신가요?{" "}
              <Link href="/login" className="hover:underline" style={{ color: 'var(--color-primary)' }}>로그인</Link>
            </p>
          )}
        </form>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--color-bg)" }}>
        <p style={{ color: "var(--color-text-muted)" }}>로딩 중...</p>
      </div>
    }>
      <SignupContent />
    </Suspense>
  );
}
