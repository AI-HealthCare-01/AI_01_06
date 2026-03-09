import re

from pydantic import BaseModel, EmailStr, field_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    name: str
    role: str = "PATIENT"
    birth_date: str | None = None
    gender: str | None = None
    phone: str | None = None
    terms_of_service: bool = False
    privacy_policy: bool = False
    marketing_consent: bool = False

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        if len(v) > 72:
            raise ValueError("비밀번호는 최대 72자 이하여야 합니다.")
        kinds = sum(
            [
                bool(re.search(r"[a-z]", v)),
                bool(re.search(r"[A-Z]", v)),
                bool(re.search(r"\d", v)),
                bool(re.search(r"[^a-zA-Z0-9]", v)),
            ]
        )
        if kinds < 3:
            raise ValueError("비밀번호는 영문 대문자, 소문자, 숫자, 특수문자 중 3종 이상을 포함해야 합니다.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
