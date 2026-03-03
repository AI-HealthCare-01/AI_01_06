"""
USER 도메인 Repository.

기준: docs/dev/Sullivan_Init.sql — users 테이블
담당 CRUD:
  - User 조회 / 생성 / 수정 / 논리 삭제
  - 이메일·닉네임·전화번호 중복 체크
  - 잠금(lock) 처리
"""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from pydantic import EmailStr

from app.core.enums import FontSizeMode, Gender, UserRole
from app.models.users import AccessibilitySetting, User

# 업데이트 허용 필드 목록
_ALLOWED_UPDATE_FIELDS: set[str] = {"name", "phone_number"}


class UserRepository:
    def __init__(self) -> None:
        self._model = User

    # ──────────────────────────────────────────
    # 조회
    # ──────────────────────────────────────────

    async def get_by_id(self, user_id: str) -> User | None:
        return await self._model.get_or_none(id=user_id, deleted_at=None)

    async def get_by_email(self, email: str | EmailStr) -> User | None:
        return await self._model.get_or_none(email=str(email), deleted_at=None)

    async def get_by_nickname(self, nickname: str) -> User | None:
        return await self._model.get_or_none(nickname=nickname, deleted_at=None)

    # ──────────────────────────────────────────
    # 중복 체크
    # ──────────────────────────────────────────

    async def exists_by_email(self, email: str | EmailStr) -> bool:
        return await self._model.filter(email=str(email)).exists()

    async def exists_by_nickname(self, nickname: str) -> bool:
        return await self._model.filter(nickname=nickname).exists()

    async def exists_by_phone_number(self, phone_number: str) -> bool:
        return await self._model.filter(phone_number=phone_number).exists()

    # ──────────────────────────────────────────
    # 생성
    # ──────────────────────────────────────────

    async def create(
        self,
        *,
        email: str | EmailStr,
        password_hash: str | None,
        name: str,
        nickname: str,
        phone_number: str | None,
        gender: Gender,
        birthdate: date,
        role: UserRole,
    ) -> User:
        return await self._model.create(
            id=str(uuid.uuid4()),
            email=str(email),
            password_hash=password_hash,
            name=name,
            nickname=nickname,
            phone_number=phone_number,
            gender=gender,
            birthdate=birthdate,
            role=role,
        )

    # ──────────────────────────────────────────
    # 수정
    # ──────────────────────────────────────────

    async def update(self, user: User, data: dict[str, Any]) -> None:
        """허용 필드만 업데이트합니다."""
        update_fields: list[str] = []
        for key, value in data.items():
            if key in _ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(user, key, value)
                update_fields.append(key)
        if update_fields:
            update_fields.append("updated_at")
            await user.save(update_fields=update_fields)

    # ──────────────────────────────────────────
    # 로그인 실패 / 잠금
    # ──────────────────────────────────────────

    async def increment_failed_attempts(self, user: User) -> None:
        user.failed_login_attempts += 1
        await user.save(update_fields=["failed_login_attempts", "updated_at"])

    async def reset_failed_attempts(self, user: User) -> None:
        user.failed_login_attempts = 0
        user.locked_until = None
        await user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

    async def lock_user(self, user: User, locked_until: datetime) -> None:
        user.locked_until = locked_until
        await user.save(update_fields=["locked_until", "updated_at"])

    # ──────────────────────────────────────────
    # 논리 삭제
    # ──────────────────────────────────────────

    async def soft_delete(self, user: User) -> None:
        """deleted_at 설정으로 논리 삭제합니다."""
        user.deleted_at = datetime.now(tz=UTC)
        await user.save(update_fields=["deleted_at", "updated_at"])


class AccessibilitySettingRepository:
    def __init__(self) -> None:
        self._model = AccessibilitySetting

    async def get_or_create(self, user_id: str) -> AccessibilitySetting:
        obj, _ = await self._model.get_or_create(user_id=user_id)
        return obj

    async def update_font_mode(self, user_id: str, font_mode: FontSizeMode) -> None:
        await self._model.filter(user_id=user_id).update(font_mode=font_mode)
