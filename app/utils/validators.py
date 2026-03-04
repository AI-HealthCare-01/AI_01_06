"""
공통 유효성 검사 함수 모음.

Pydantic AfterValidator 와 함께 사용하거나 서비스 레이어에서 직접 호출합니다.
모든 함수는 값이 유효하면 그대로 반환하고, 유효하지 않으면 ValueError 를 발생시킵니다.
"""

import re
from datetime import date

# ──────────────────────────────────────────
# 비밀번호
# ──────────────────────────────────────────

_PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,}$")


def validate_password(value: str) -> str:
    """
    비밀번호 검증 규칙:
    - 최소 8자 이상
    - 영문 대/소문자, 숫자, 특수문자를 각각 1자 이상 포함
    """
    if not _PASSWORD_PATTERN.match(value):
        raise ValueError("비밀번호는 8자 이상이며 영문 대/소문자, 숫자, 특수문자를 각각 1자 이상 포함해야 합니다.")
    return value


# ──────────────────────────────────────────
# 생년월일
# ──────────────────────────────────────────

_MIN_AGE = 1
_MAX_AGE = 120


def validate_birthday(value: date) -> date:
    """
    생년월일 검증 규칙:
    - 미래 날짜 불허
    - 1세 이상 120세 이하
    """
    today = date.today()
    if value >= today:
        raise ValueError("생년월일은 오늘 이전 날짜여야 합니다.")

    age = (today - value).days // 365
    if age < _MIN_AGE:
        raise ValueError(f"생년월일 기준 나이가 {_MIN_AGE}세 미만입니다.")
    if age > _MAX_AGE:
        raise ValueError(f"생년월일 기준 나이가 {_MAX_AGE}세를 초과합니다.")

    return value


# ──────────────────────────────────────────
# 전화번호
# ──────────────────────────────────────────

_PHONE_STRIP_PATTERN = re.compile(r"[\s\-\.]")
_PHONE_VALID_PATTERN = re.compile(r"^(010|011|016|017|018|019)\d{7,8}$")


def validate_phone_number(value: str) -> str:
    """
    전화번호 검증 규칙:
    - 공백·하이픈·점 제거 후 검사
    - 한국 휴대폰 번호 형식: 010~019 로 시작, 10~11자리
    """
    normalized = _PHONE_STRIP_PATTERN.sub("", value)
    if not _PHONE_VALID_PATTERN.match(normalized):
        raise ValueError("유효한 한국 휴대폰 번호를 입력해주세요. (예: 010-1234-5678)")
    return normalized


def normalize_phone_number(value: str) -> str:
    """
    전화번호를 숫자만 남기도록 정규화합니다.
    검증 없이 순수 변환만 수행합니다.
    """
    return _PHONE_STRIP_PATTERN.sub("", value)
