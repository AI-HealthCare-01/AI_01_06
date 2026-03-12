export type FieldErrorKey =
  | "email"
  | "nickname"
  | "password"
  | "passwordConfirm"
  | "name"
  | "birth_date"
  | "gender"
  | "phonePrefix"
  | "phoneMiddle"
  | "phoneLast"
  | "terms"
  | "privacy";

export type PhoneState = {
  prefix: string;
  prefixCustom: string;
  middle: string;
  last: string;
};

export function validateEmail(value: string): string | null {
  if (!value.trim()) return "이메일을 입력해주세요.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "올바른 이메일 형식을 입력해주세요.";
  return null;
}

export function validateNickname(value: string): string | null {
  if (!value.trim()) return "별명을 입력해주세요.";
  if (value.length < 2) return "별명은 2자 이상이어야 합니다.";
  if (value.length > 20) return "별명은 20자 이하로 입력해주세요.";
  if (!/^[가-힣a-zA-Z0-9]+$/.test(value)) return "별명은 한글, 영문, 숫자만 사용할 수 있습니다.";
  return null;
}

// KISA 비밀번호 선택 및 이용 안내서 (2020) 옵션 A: 2종 이상 조합 + 10자 이상
// 개인정보보호위원회 고시(2023) 제5조 준용
export function validatePassword(value: string): string | null {
  if (!value) return "비밀번호를 입력해주세요.";
  if (value.length < 10) return "비밀번호는 10자 이상이어야 합니다.";
  if (value.length > 128) return "비밀번호는 128자 이하로 입력해주세요.";
  const hasLetter = /[a-zA-Z]/.test(value);
  const hasDigit = /[0-9]/.test(value);
  const hasSpecial = /[^a-zA-Z0-9]/.test(value);
  const typeCount = [hasLetter, hasDigit, hasSpecial].filter(Boolean).length;
  if (typeCount < 2) return "영문, 숫자, 특수문자 중 2종 이상을 포함해야 합니다.";
  return null;
}

export function getPasswordStrength(value: string): "weak" | "fair" | "strong" {
  if (!value || value.length < 10) return "weak";
  if (value.length >= 16) return "strong";
  return "fair";
}

export function validatePasswordConfirm(password: string, confirm: string): string | null {
  if (!confirm) return "비밀번호 확인을 입력해주세요.";
  if (password !== confirm) return "비밀번호가 일치하지 않습니다.";
  return null;
}

export function validateName(value: string): string | null {
  if (!value.trim()) return "이름을 입력해주세요.";
  if (value.trim().length < 2) return "이름은 2자 이상이어야 합니다.";
  if (!/^[가-힣a-zA-Z\s]+$/.test(value.trim())) return "이름은 한글 또는 영문으로 입력해주세요.";
  return null;
}

export function validateBirthDate(value: string): string | null {
  if (!value) return "생년월일을 입력해주세요.";
  const date = new Date(value);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (date > today) return "미래 날짜는 입력할 수 없습니다.";
  const minDate = new Date(today.getFullYear() - 100, today.getMonth(), today.getDate());
  if (date < minDate) return "유효한 생년월일을 입력해주세요.";
  return null;
}

export function validateGender(value: string): string | null {
  if (!value) return "성별을 선택해주세요.";
  return null;
}

export function validatePhonePrefix(prefix: string, custom: string): string | null {
  if (prefix === "직접입력" && custom.replace(/\D/g, "").length < 2)
    return "앞자리 번호를 입력해주세요.";
  return null;
}

export function validatePhoneMiddle(value: string): string | null {
  if (value.length < 4) return "중간 번호 4자리를 입력해주세요.";
  return null;
}

export function validatePhoneLast(value: string): string | null {
  if (value.length < 4) return "끝 번호 4자리를 입력해주세요.";
  return null;
}

export function validateAllFields(params: {
  form: Record<string, string>;
  phoneState: PhoneState;
  socialData: { provider: string } | null;
  agreements: { terms: boolean; privacy: boolean };
}): Partial<Record<FieldErrorKey, string>> {
  const { form, phoneState, socialData, agreements } = params;
  const errors: Partial<Record<FieldErrorKey, string>> = {};

  const set = (k: FieldErrorKey, fn: () => string | null) => {
    const e = fn();
    if (e) errors[k] = e;
  };

  set("email", () => validateEmail(form.email ?? ""));
  set("nickname", () => validateNickname(form.nickname ?? ""));

  if (!socialData) {
    set("password", () => validatePassword(form.password ?? ""));
    set("passwordConfirm", () =>
      validatePasswordConfirm(form.password ?? "", form.passwordConfirm ?? ""),
    );
  }

  set("name", () => validateName(form.name ?? ""));
  set("birth_date", () => validateBirthDate(form.birth_date ?? ""));
  set("gender", () => validateGender(form.gender ?? ""));
  set("phonePrefix", () => validatePhonePrefix(phoneState.prefix, phoneState.prefixCustom));
  set("phoneMiddle", () => validatePhoneMiddle(phoneState.middle));
  set("phoneLast", () => validatePhoneLast(phoneState.last));

  if (!agreements.terms) errors.terms = "이용약관에 동의해주세요.";
  if (!agreements.privacy) errors.privacy = "개인정보 처리방침에 동의해주세요.";

  return errors;
}
