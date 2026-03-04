"""
USER 도메인 DTO.

기준: docs/dev/api_spec.md
  - GET  /api/users/me          (내 정보 조회)
  - PATCH /api/users/me         (내 정보 수정)
  - PATCH /api/users/me/accessibility (접근성 설정 변경)
  - DELETE /api/users/me        (회원 탈퇴)
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.core.enums import FontSizeMode, Gender, UserRole
from app.dtos.base import BaseSerializerModel
from app.utils.validators import validate_phone_number

# ──────────────────────────────────────────
# 내 정보 수정
# ──────────────────────────────────────────


class UserUpdateRequest(BaseModel):
    """PATCH /api/users/me 요청 바디. 모든 필드 선택적."""

    name: Annotated[
        str | None,
        Field(None, min_length=1, max_length=100, description="이름"),
    ]
    phone_number: Annotated[
        str | None,
        Field(None, description="휴대폰 번호 (예: 010-1234-5678)"),
        AfterValidator(lambda v: validate_phone_number(v) if v is not None else v),
    ]


# ──────────────────────────────────────────
# 접근성 설정 변경
# ──────────────────────────────────────────


class AccessibilityUpdateRequest(BaseModel):
    """PATCH /api/users/me/accessibility 요청 바디.

    REQ-COM-001: 고령층을 배려한 글자 크기 모드 토글.
    """

    font_mode: Annotated[FontSizeMode, Field(..., description="글자 크기 모드 (SMALL | LARGE)")]


# ──────────────────────────────────────────
# 내 정보 조회 응답
# ──────────────────────────────────────────


class UserInfoResponse(BaseSerializerModel):
    """GET /api/users/me 응답 바디."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    email: str
    name: str
    nickname: str
    phone_number: str | None = None
    gender: Gender
    birthdate: date
    role: UserRole
    font_size_mode: FontSizeMode | None = None
    created_at: datetime
