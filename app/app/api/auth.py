from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.deps import get_current_user, security_scheme
from app.core.rate_limit import limiter
from app.core.redis import get_state_redis
from app.core.response import error_response, success_response
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.auth_provider import AuthProvider
from app.models.patient_profile import PatientProfile
from app.models.refresh_token import RefreshToken
from app.models.terms_consent import TermsConsent
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest
from app.services.audit_service import log_action

router = APIRouter(prefix="/api/auth", tags=["auth"])

_MAX_LOGIN_ATTEMPTS = 5


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/signup")
@limiter.limit("5/hour")
async def signup(request: Request, req: SignupRequest):
    if not req.terms_of_service or not req.privacy_policy:
        return error_response("필수 약관(이용약관, 개인정보처리방침)에 동의해야 합니다.")

    existing = await User.filter(email=req.email).first()
    if existing:
        if existing.deleted_at:
            return error_response("삭제 대기중인 이메일 주소입니다.")
        return error_response("이미 가입된 이메일주소입니다.")

    existing_nick = await User.filter(nickname=req.nickname).first()
    if existing_nick:
        if existing_nick.deleted_at:
            return error_response("삭제 대기중인 닉네임입니다.")
        return error_response("이미 사용 중인 닉네임입니다.")

    birth = date.fromisoformat(req.birth_date) if req.birth_date else None

    user = await User.create(
        email=req.email,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
        name=req.name,
        role=req.role,
        birth_date=birth,
        gender=req.gender,
        phone=req.phone,
    )
    await AuthProvider.create(user=user, provider="LOCAL", provider_user_id=req.email)
    await TermsConsent.create(
        user=user,
        terms_of_service=req.terms_of_service,
        privacy_policy=req.privacy_policy,
        marketing_consent=req.marketing_consent,
    )
    if user.role == "PATIENT":
        await PatientProfile.create(user=user)
    return success_response({"id": user.id, "email": user.email, "nickname": user.nickname, "role": user.role})


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest):
    ip = request.client.host if request.client else "unknown"
    user = await User.filter(email=req.email, deleted_at__isnull=True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="계정이 잠겨 있습니다. 잠시 후 다시 시도하세요."
        )

    if not verify_password(req.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= _MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
        await user.save()
        await log_action(user.id, "LOGIN", ip, outcome="FAILURE")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    await user.save()
    await log_action(user.id, "LOGIN", ip)

    return success_response(
        {
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": await create_refresh_token(user.id),
            "token_type": "bearer",
        }
    )


@router.post("/refresh")
@limiter.limit("5/minute")
async def refresh(request: Request, req: RefreshRequest):
    # atomic update로 race condition 방지 (double-spend 차단)
    updated = await RefreshToken.filter(token=req.refresh_token, revoked=False).update(revoked=True)
    if updated == 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 refresh token입니다.")
    rt = await RefreshToken.get(token=req.refresh_token)
    if rt.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 refresh token입니다.")
    user = await User.get_or_none(id=rt.user_id, deleted_at__isnull=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")
    return success_response(
        {
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": await create_refresh_token(user.id),
            "token_type": "bearer",
        }
    )


@router.post("/logout")
async def logout(
    req: LogoutRequest | None = None,
    user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    payload = decode_token(credentials.credentials)
    jti = payload.get("jti") if payload else None
    if jti:
        redis = await get_state_redis()
        remaining_ttl = max(1, int(payload["exp"] - datetime.now(UTC).timestamp()))
        await redis.setex(f"blacklist:{jti}", remaining_ttl, "1")
    if req and req.refresh_token:
        await RefreshToken.filter(token=req.refresh_token, user_id=user.id).update(revoked=True)
    else:
        await RefreshToken.filter(user_id=user.id, revoked=False).update(revoked=True)
    return success_response({"message": "로그아웃 되었습니다."})
