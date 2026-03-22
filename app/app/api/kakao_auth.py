import json
import secrets
from datetime import date

import httpx
from fastapi import APIRouter

from app import config
from app.core.redis import get_state_redis
from app.core.response import error_response, success_response
from app.core.security import create_access_token, create_refresh_token
from app.models.auth_provider import AuthProvider
from app.models.patient_profile import PatientProfile
from app.models.terms_consent import TermsConsent
from app.models.user import User
from app.schemas.auth import KakaoCallbackRequest, KakaoRegisterRequest
from app.services.kakao_service import get_kakao_service

router = APIRouter(prefix="/api/auth/kakao", tags=["kakao-auth"])

_STATE_TTL = 300  # 5분
_PENDING_TTL = 600  # 10분


@router.get("/url")
async def kakao_authorize_url():
    state = secrets.token_urlsafe(32)
    redis = await get_state_redis()
    await redis.set(f"kakao:state:{state}", "1", ex=_STATE_TTL)

    url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={config.KAKAO_CLIENT_ID}"
        f"&redirect_uri={config.KAKAO_REDIRECT_URI}"
        "&response_type=code"
        f"&state={state}"
        "&scope=profile_nickname"
    )
    return success_response({"url": url, "state": state})


@router.post("/callback")
async def kakao_callback(req: KakaoCallbackRequest):
    redis = await get_state_redis()

    # CSRF state 검증
    state_key = f"kakao:state:{req.state}"
    if not await redis.get(state_key):
        return error_response("유효하지 않거나 만료된 요청입니다.")
    await redis.delete(state_key)

    # Kakao API 호출
    kakao_svc = get_kakao_service()
    try:
        token_data = await kakao_svc.exchange_code(req.code)
        kakao_user = await kakao_svc.get_user_info(token_data["access_token"])
    except httpx.HTTPStatusError as e:
        return error_response(f"Kakao 인증 실패 ({e.response.status_code})")
    except httpx.RequestError:
        return error_response("Kakao 서버 연결에 실패했습니다.")

    kakao_id = str(kakao_user["id"])
    kakao_account = kakao_user.get("kakao_account", {})
    kakao_email = kakao_account.get("email") or ""
    kakao_nickname = kakao_account.get("profile", {}).get("nickname", "")

    # 기존 Kakao 사용자 확인
    provider = await AuthProvider.filter(provider="KAKAO", provider_user_id=kakao_id).select_related("user").first()
    if provider:
        user = provider.user
        if user.deleted_at:
            return error_response("삭제 대기중인 계정입니다.")
        return success_response(
            {
                "status": "login",
                "access_token": create_access_token(user.id, user.role),
                "refresh_token": await create_refresh_token(user.id),
                "token_type": "bearer",
            }
        )

    # 이메일 충돌 확인 (Kakao가 이메일 제공한 경우만)
    if kakao_email:
        existing = await User.filter(email=kakao_email).first()
        if existing:
            if existing.deleted_at:
                return error_response("삭제 대기중인 이메일 주소입니다.")
            return error_response("이미 가입된 이메일주소입니다.")

    # 신규 사용자 — registration_token 발급
    registration_token = secrets.token_urlsafe(32)
    pending_data = json.dumps({"kakao_id": kakao_id, "kakao_email": kakao_email, "kakao_nickname": kakao_nickname})
    await redis.set(f"kakao:pending:{registration_token}", pending_data, ex=_PENDING_TTL)

    return success_response(
        {
            "status": "new_user",
            "registration_token": registration_token,
            "kakao_profile": {"email": kakao_email, "nickname": kakao_nickname},
        }
    )


@router.post("/register")
async def kakao_register(req: KakaoRegisterRequest):
    if not req.terms_of_service or not req.privacy_policy:
        return error_response("필수 약관(이용약관, 개인정보처리방침)에 동의해야 합니다.")

    redis = await get_state_redis()
    token_key = f"kakao:pending:{req.registration_token}"
    raw = await redis.get(token_key)
    if not raw:
        return error_response("유효하지 않거나 만료된 가입 토큰입니다.")

    pending = json.loads(raw)
    kakao_id: str = pending["kakao_id"]

    # 이메일 중복 재확인 (register 시점 race condition 방지)
    existing = await User.filter(email=req.email).first()
    if existing:
        if existing.deleted_at:
            return error_response("삭제 대기중인 이메일 주소입니다.")
        return error_response("이미 가입된 이메일주소입니다.")

    # kakao_id 중복 확인 (동시 요청 방지)
    if await AuthProvider.filter(provider="KAKAO", provider_user_id=kakao_id).exists():
        return error_response("이미 카카오로 가입된 계정이 있습니다.")

    # 닉네임 중복 확인
    existing_nick = await User.filter(nickname=req.nickname).first()
    if existing_nick:
        if existing_nick.deleted_at:
            return error_response("삭제 대기중인 닉네임입니다.")
        return error_response("이미 사용 중인 닉네임입니다.")

    birth = date.fromisoformat(req.birth_date) if req.birth_date else None

    user = await User.create(
        email=req.email,
        password_hash=None,
        nickname=req.nickname,
        name=req.name,
        role=req.role,
        birth_date=birth,
        gender=req.gender,
        phone=req.phone,
    )
    await AuthProvider.create(user=user, provider="KAKAO", provider_user_id=kakao_id)
    # 토큰 삭제: 가입 성공 후 소멸 — 검증 실패 시 재시도 허용 (DB unique 제약이 동시 요청 방어)
    await redis.delete(token_key)
    await TermsConsent.create(
        user=user,
        terms_of_service=req.terms_of_service,
        privacy_policy=req.privacy_policy,
        marketing_consent=req.marketing_consent,
    )
    if user.role == "PATIENT":
        await PatientProfile.create(user=user)

    return success_response(
        {
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": await create_refresh_token(user.id),
            "token_type": "bearer",
        }
    )
