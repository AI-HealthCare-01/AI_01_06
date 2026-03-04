"""
AUTH 도메인 DTO.

기준: docs/dev/api_spec.md
  - POST /api/auth/signup
  - POST /api/auth/login
  - POST /api/auth/refresh
  - POST /api/auth/logout
"""

from datetime import date
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import Gender, UserRole
from app.utils.validators import validate_birthday, validate_password, validate_phone_number

# ──────────────────────────────────────────
# 회원가입
# ──────────────────────────────────────────


class SignUpRequest(BaseModel):
    """POST /api/auth/signup 요청 바디.

    REQ-USR-001: 이메일, 비밀번호, 이름, 성별, 생년월일, 휴대폰 번호 등 기본 폼 입력.
    REQ-COM-002: 역할(PATIENT | GUARDIAN) 분기 가입.
    """

    model_config = ConfigDict(populate_by_name=True)

    email: Annotated[
        EmailStr,
        Field(..., max_length=255, description="이메일 (고유)"),
    ]
    password: Annotated[
        str,
        Field(..., min_length=8, description="비밀번호 (8자 이상, 대/소/숫자/특수문자 포함)"),
        AfterValidator(validate_password),
    ]
    name: Annotated[str, Field(..., max_length=100, description="이름")]
    nickname: Annotated[str, Field(..., max_length=50, description="닉네임 (고유, 보호자-환자 검색용)")]
    phone_number: Annotated[
        str,
        Field(..., description="휴대폰 번호 (예: 010-1234-5678)"),
        AfterValidator(validate_phone_number),
    ]
    gender: Annotated[Gender, Field(..., description="성별 (M | F)")]
    birthdate: Annotated[
        date,
        Field(..., description="생년월일 (YYYY-MM-DD)"),
        AfterValidator(validate_birthday),
    ]
    role: Annotated[UserRole, Field(..., description="역할 (PATIENT | GUARDIAN)")]


# ──────────────────────────────────────────
# 로그인
# ──────────────────────────────────────────


class LoginRequest(BaseModel):
    """POST /api/auth/login 요청 바디."""

    email: EmailStr
    password: Annotated[str, Field(..., min_length=8)]


class LoginResponse(BaseModel):
    """POST /api/auth/login 응답 바디.

    refresh_token은 httpOnly 쿠키로 설정되므로 응답 바디에 포함하지 않습니다.
    """

    access_token: str
    role: UserRole


# ──────────────────────────────────────────
# 토큰 재발급
# ──────────────────────────────────────────


class TokenRefreshResponse(BaseModel):
    """POST /api/auth/refresh 응답 바디."""

    access_token: str
