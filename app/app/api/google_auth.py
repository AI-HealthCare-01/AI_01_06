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
from app.schemas.auth import GoogleCallbackRequest, GoogleRegisterRequest
from app.services.google_service import get_google_service

router = APIRouter(prefix="/api/auth/google", tags=["google-auth"])

_STATE_TTL = 300  # 5분
_PENDING_TTL = 600  # 10분


@router.get("/url")
async def google_authorize_url():
    state = secrets.token_urlsafe(32)
    redis = await get_state_redis()
    await redis.set(f"google:state:{state}", "1", ex=_STATE_TTL)

    # prompt=select_account: 이미 로그인된 계정이 있어도 계정 선택 화면 강제 표시
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={config.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={config.GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        f"&state={state}"
        "&scope=openid%20email%20profile"
        "&prompt=select_account"
    )
    return success_response({"url": url, "state": state})


@router.post("/callback")
async def google_callback(req: GoogleCallbackRequest):
    redis = await get_state_redis()

    # CSRF state 검증 (일회용)
    state_key = f"google:state:{req.state}"
    if not await redis.get(state_key):
        return error_response("유효하지 않거나 만료된 요청입니다.")
    await redis.delete(state_key)

    google_svc = get_google_service()
    try:
        token_data = await google_svc.exchange_code(req.code)
        google_user = await google_svc.get_user_info(token_data["access_token"])
    except httpx.HTTPStatusError as e:
        return error_response(f"Google 인증 실패 ({e.response.status_code})")
    except httpx.RequestError:
        return error_response("Google 서버 연결에 실패했습니다.")

    google_id = google_user["sub"]  # Google 안정적 ID (이메일 변경에도 불변)
    google_email = google_user.get("email", "")
    google_name = google_user.get("name", "")  # 표시 이름 → 닉네임 + 이름 자동 채우기

    # 기존 Google 사용자 확인 (provider ID 기반 — email_verified 불필요)
    provider = await AuthProvider.filter(provider="GOOGLE", provider_user_id=google_id).select_related("user").first()
    if provider:
        user = provider.user
        return success_response(
            {
                "status": "login",
                "access_token": create_access_token(user.id, user.role),
                "refresh_token": create_refresh_token(user.id),
                "token_type": "bearer",
            }
        )

    # OpenID Connect Core 1.0 §5.1: 신규 가입 시 email_verified=false 차단
    # 의료 서비스에서 미인증 이메일로 계정 생성 허용 불가 (OWASP ASVS V2.5.6)
    if not google_user.get("email_verified", False):
        return error_response("이메일 인증이 완료되지 않은 Google 계정입니다.")

    # 이메일 충돌 확인 (다른 provider로 이미 가입된 경우)
    if google_email and await User.filter(email=google_email).exists():
        return error_response("이미 해당 이메일로 가입된 계정이 있습니다. 이메일 로그인을 이용하세요.")

    # 신규 사용자 — registration_token 발급
    registration_token = secrets.token_urlsafe(32)
    pending_data = json.dumps(
        {
            "google_id": google_id,
            "google_email": google_email,
            "google_name": google_name,
        }
    )
    await redis.set(f"google:pending:{registration_token}", pending_data, ex=_PENDING_TTL)

    return success_response(
        {
            "status": "new_user",
            "registration_token": registration_token,
            # email, nickname, name 모두 전달 → 회원가입 폼 자동 채우기
            "google_profile": {
                "email": google_email,
                "nickname": google_name,
                "name": google_name,
            },
        }
    )


@router.post("/register")
async def google_register(req: GoogleRegisterRequest):
    if not req.terms_of_service or not req.privacy_policy:
        return error_response("필수 약관(이용약관, 개인정보처리방침)에 동의해야 합니다.")

    redis = await get_state_redis()
    token_key = f"google:pending:{req.registration_token}"
    raw = await redis.get(token_key)
    if not raw:
        return error_response("유효하지 않거나 만료된 가입 토큰입니다.")

    pending = json.loads(raw)
    google_id: str = pending["google_id"]
    await redis.delete(token_key)  # 일회용

    # 이메일 중복 재확인 (register 시점 race condition 방지)
    if await User.filter(email=req.email).exists():
        return error_response("이미 사용 중인 이메일입니다.")

    # google_id 중복 확인 (동시 요청 방지)
    if await AuthProvider.filter(provider="GOOGLE", provider_user_id=google_id).exists():
        return error_response("이미 구글로 가입된 계정이 있습니다.")

    if await User.filter(nickname=req.nickname).exists():
        return error_response("이미 사용 중인 닉네임입니다.")

    birth = date.fromisoformat(req.birth_date) if req.birth_date else None

    user = await User.create(
        email=req.email,
        password_hash=None,  # 소셜 전용 계정
        nickname=req.nickname,
        name=req.name,
        role=req.role,
        birth_date=birth,
        gender=req.gender,
        phone=req.phone,
    )
    await AuthProvider.create(user=user, provider="GOOGLE", provider_user_id=google_id)
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
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }
    )
