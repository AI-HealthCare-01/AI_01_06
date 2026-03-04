"""
USER 도메인 Service.

기준: docs/dev/api_spec.md
  - GET    /api/users/me              (내 정보 조회)
  - PATCH  /api/users/me              (내 정보 수정)
  - PATCH  /api/users/me/accessibility (접근성 설정 변경)
  - DELETE /api/users/me              (회원 탈퇴)
"""

from fastapi import HTTPException
from starlette import status
from tortoise.transactions import in_transaction

from app.dtos.users import AccessibilityUpdateRequest, UserUpdateRequest
from app.models.users import User
from app.repositories.user_repository import AccessibilitySettingRepository, UserRepository


class UserService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.accessibility_repo = AccessibilitySettingRepository()

    # ──────────────────────────────────────────
    # 내 정보 조회
    # ──────────────────────────────────────────

    async def get_me(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )
        return user

    # ──────────────────────────────────────────
    # 내 정보 수정
    # ──────────────────────────────────────────

    async def update_me(self, user: User, data: UserUpdateRequest) -> User:
        update_data: dict = {}

        if data.name is not None:
            update_data["name"] = data.name

        if data.phone_number is not None:
            # 전화번호 중복 체크 (자신 제외)
            existing = await self.user_repo.exists_by_phone_number(data.phone_number)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 사용 중인 휴대폰 번호입니다.",
                )
            update_data["phone_number"] = data.phone_number

        async with in_transaction():
            await self.user_repo.update(user=user, data=update_data)
            await user.refresh_from_db()

        return user

    # ──────────────────────────────────────────
    # 접근성 설정 변경
    # ──────────────────────────────────────────

    async def update_accessibility(self, user_id: str, data: AccessibilityUpdateRequest) -> None:
        """REQ-COM-001: 고령층을 배려한 글자 크기 모드 토글."""
        await self.accessibility_repo.update_font_mode(user_id=user_id, font_mode=data.font_mode)

    # ──────────────────────────────────────────
    # 회원 탈퇴
    # ──────────────────────────────────────────

    async def withdraw_me(self, user: User) -> None:
        """논리 삭제 처리. deleted_at 설정."""
        async with in_transaction():
            await self.user_repo.soft_delete(user)
