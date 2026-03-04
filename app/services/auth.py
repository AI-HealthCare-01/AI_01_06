"""
AUTH 도메인 Service.

기준: docs/dev/api_spec.md
  - POST /api/auth/signup   (REQ-USR-001, REQ-COM-002)
  - POST /api/auth/login    (REQ-USR-008)
  - POST /api/auth/refresh
  - POST /api/auth/logout
"""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from starlette import status
from tortoise.transactions import in_transaction

from app.dtos.auth import LoginRequest, SignUpRequest
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.jwt import JwtService
from app.utils.jwt.tokens import AccessToken, RefreshToken
from app.utils.security import hash_password, verify_password

# 로그인 실패 잠금 설정
_MAX_FAILED_ATTEMPTS = 5
_LOCK_DURATION_MINUTES = 30


class AuthService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.jwt_service = JwtService()

    # ──────────────────────────────────────────
    # 회원가입
    # ──────────────────────────────────────────

    async def signup(self, data: SignUpRequest) -> User:
        """REQ-USR-001: 이메일, 비밀번호, 이름, 성별, 생년월일, 휴대폰 번호 등 기본 폼 입력."""
        await self._check_email_unique(data.email)
        await self._check_nickname_unique(data.nickname)
        if data.phone_number:
            await self._check_phone_unique(data.phone_number)

        async with in_transaction():
            user = await self.user_repo.create(
                email=data.email,
                password_hash=hash_password(data.password),
                name=data.name,
                nickname=data.nickname,
                phone_number=data.phone_number,
                gender=data.gender,
                birthdate=data.birthdate,
                role=data.role,
            )
        return user

    # ──────────────────────────────────────────
    # 로그인
    # ──────────────────────────────────────────

    async def authenticate(self, data: LoginRequest) -> User:
        """REQ-USR-008: 이메일과 비밀번호를 통한 로그인."""
        user = await self.user_repo.get_by_email(str(data.email))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            )

        # 계정 잠금 체크
        if user.locked_until and user.locked_until > datetime.now(tz=UTC):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"계정이 잠겼습니다. {user.locked_until.strftime('%Y-%m-%d %H:%M')} 이후 다시 시도해주세요.",
            )

        # 비밀번호 검증
        if not user.password_hash or not verify_password(data.password, user.password_hash):
            await self.user_repo.increment_failed_attempts(user)
            if user.failed_login_attempts + 1 >= _MAX_FAILED_ATTEMPTS:
                locked_until = datetime.now(tz=UTC) + timedelta(minutes=_LOCK_DURATION_MINUTES)
                await self.user_repo.lock_user(user, locked_until)
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"로그인 실패 {_MAX_FAILED_ATTEMPTS}회로 계정이 {_LOCK_DURATION_MINUTES}분간 잠겼습니다.",
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            )

        # 논리 삭제된 계정 체크
        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="탈퇴한 계정입니다.",
            )

        # 로그인 성공 시 실패 횟수 초기화
        if user.failed_login_attempts > 0:
            await self.user_repo.reset_failed_attempts(user)

        return user

    async def login(self, user: User) -> dict[str, AccessToken | RefreshToken]:
        return self.jwt_service.issue_jwt_pair(user)

    # ──────────────────────────────────────────
    # 중복 체크 (내부용)
    # ──────────────────────────────────────────

    async def _check_email_unique(self, email: str) -> None:
        if await self.user_repo.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 이메일입니다.",
            )

    async def _check_nickname_unique(self, nickname: str) -> None:
        if await self.user_repo.exists_by_nickname(nickname):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 닉네임입니다.",
            )

    async def _check_phone_unique(self, phone_number: str) -> None:
        if await self.user_repo.exists_by_phone_number(phone_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 휴대폰 번호입니다.",
            )
