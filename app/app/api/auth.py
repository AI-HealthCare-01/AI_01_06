from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.response import error_response, success_response
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.auth_provider import AuthProvider
from app.models.terms_consent import TermsConsent
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
async def signup(req: SignupRequest):
    if not req.terms_of_service or not req.privacy_policy:
        return error_response("필수 약관(이용약관, 개인정보처리방침)에 동의해야 합니다.")

    existing = await User.filter(email=req.email).first()
    if existing:
        return error_response("이미 등록된 이메일입니다.")

    birth = None
    if req.birth_date:
        birth = date.fromisoformat(req.birth_date)

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
    await AuthProvider.create(
        user=user,
        provider="LOCAL",
        provider_user_id=req.email,
    )
    await TermsConsent.create(
        user=user,
        terms_of_service=req.terms_of_service,
        privacy_policy=req.privacy_policy,
        marketing_consent=req.marketing_consent,
    )
    return success_response(
        {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role,
        }
    )


@router.post("/login")
async def login(req: LoginRequest):
    user = await User.filter(email=req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    )


@router.post("/refresh")
async def refresh(token: dict):
    payload = decode_token(token.get("refresh_token", ""))
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = int(payload["sub"])
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    return success_response(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    )


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    return success_response({"message": "로그아웃 되었습니다."})
