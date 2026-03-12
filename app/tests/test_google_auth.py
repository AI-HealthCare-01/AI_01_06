import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.auth_provider import AuthProvider
from app.models.patient_profile import PatientProfile
from app.models.terms_consent import TermsConsent
from app.models.user import User

# ---------------------------------------------------------------------------
# Phase 1 — GET /api/auth/google/url
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_google_url_returns_authorization_url(client: AsyncClient):
    """GET /api/auth/google/url 은 Google 인증 URL과 state를 반환한다."""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)

    with patch("app.api.google_auth.get_state_redis", return_value=mock_redis):
        resp = await client.get("/api/auth/google/url")

    body = resp.json()
    assert body["success"] is True
    assert "accounts.google.com/o/oauth2/v2/auth" in body["data"]["url"]
    assert "redirect_uri" in body["data"]["url"]
    assert "select_account" in body["data"]["url"]
    assert "state" in body["data"]


# ---------------------------------------------------------------------------
# Phase 2 — POST /api/auth/google/callback: CSRF state 검증
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_google_callback_rejects_invalid_state(client: AsyncClient):
    """만료/없는 state → CSRF 방어로 에러 반환."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.api.google_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post("/api/auth/google/callback", json={"code": "code", "state": "tampered"})

    body = resp.json()
    assert body["success"] is False


# ---------------------------------------------------------------------------
# Phase 3 — POST /api/auth/google/callback: 기존 사용자
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_google_callback_logs_in_existing_google_user(client: AsyncClient):
    """이미 Google로 가입한 사용자 → JWT 즉시 발급."""
    user = await User.create(email="google@test.com", nickname="구글유저", name="구글유저", password_hash=None)
    await AuthProvider.create(user=user, provider="GOOGLE", provider_user_id="google-sub-9999")
    await TermsConsent.create(user=user, terms_of_service=True, privacy_policy=True)

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "google_tok"}
    mock_svc.get_user_info.return_value = {
        "sub": "google-sub-9999",
        "email": "google@test.com",
        "name": "구글유저",
    }

    with (
        patch("app.api.google_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.google_auth.get_google_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/google/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "login"
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


# ---------------------------------------------------------------------------
# Phase 4 — POST /api/auth/google/callback: 이메일 충돌 + 신규 사용자
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_google_callback_rejects_email_conflict(client: AsyncClient):
    """다른 provider로 가입된 이메일로 Google 로그인 시도 → 에러."""
    existing = await User.create(email="conflict@test.com", nickname="기존유저", name="기존", password_hash="hashed")
    await AuthProvider.create(user=existing, provider="LOCAL", provider_user_id="conflict@test.com")

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "sub": "google-sub-8888",
        "email": "conflict@test.com",
        "name": "구글",
    }

    with (
        patch("app.api.google_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.google_auth.get_google_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/google/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is False
    assert "이메일" in body["error"]


@pytest.mark.asyncio
async def test_google_callback_new_user_returns_registration_token_and_profile(
    client: AsyncClient,
):
    """신규 Google 사용자 → registration_token + email/nickname/name 모두 반환."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()
    mock_redis.set = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "sub": "google-sub-7777",
        "email": "new@gmail.com",
        "name": "홍길동",
    }

    with (
        patch("app.api.google_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.google_auth.get_google_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/google/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "new_user"
    assert "registration_token" in body["data"]
    profile = body["data"]["google_profile"]
    assert profile["email"] == "new@gmail.com"
    assert profile["nickname"] == "홍길동"
    assert profile["name"] == "홍길동"


# ---------------------------------------------------------------------------
# S1 — POST /api/auth/google/callback: email_verified 미인증 거부
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_google_callback_rejects_unverified_email(client: AsyncClient):
    """email_verified=false Google 계정 → 미인증 이메일 가입 거부 (OpenID Connect spec)."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "sub": "google-sub-unverified",
        "email": "unverified@gmail.com",
        "email_verified": False,
        "name": "미인증",
    }

    with (
        patch("app.api.google_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.google_auth.get_google_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/google/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is False
    assert "이메일" in body["error"]


# ---------------------------------------------------------------------------
# Phase 5 — POST /api/auth/google/register
# ---------------------------------------------------------------------------

_REGISTER_BASE = {
    "registration_token": "valid-token",
    "email": "reg@gmail.com",
    "name": "홍길동",
    "nickname": "구글닉",
    "role": "PATIENT",
    "terms_of_service": True,
    "privacy_policy": True,
}


def _make_pending(google_id: str = "google-sub-5555", email: str = "reg@gmail.com") -> str:
    return json.dumps(
        {
            "google_id": google_id,
            "google_email": email,
            "google_name": "홍길동",
        }
    )


@pytest.mark.asyncio
async def test_google_register_creates_user_and_returns_tokens(client: AsyncClient):
    """유효한 token + 완전한 폼 → 사용자 생성 + JWT 발급 + DB 4중 검증."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=_make_pending())
    mock_redis.delete = AsyncMock()

    with patch("app.api.google_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post("/api/auth/google/register", json=_REGISTER_BASE)

    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]

    user = await User.filter(email="reg@gmail.com").first()
    assert user is not None
    assert user.password_hash is None  # 소셜 전용 계정
    assert user.name == "홍길동"

    provider = await AuthProvider.filter(user=user, provider="GOOGLE").first()
    assert provider is not None
    assert provider.provider_user_id == "google-sub-5555"

    consent = await TermsConsent.filter(user=user).first()
    assert consent is not None
    assert consent.terms_of_service is True

    profile = await PatientProfile.filter(user=user).first()
    assert profile is not None  # PATIENT → PatientProfile 자동 생성


@pytest.mark.asyncio
async def test_google_register_rejects_invalid_token(client: AsyncClient):
    """만료/없는 registration_token → 에러."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.api.google_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/google/register",
            json={**_REGISTER_BASE, "registration_token": "expired"},
        )

    assert resp.json()["success"] is False


@pytest.mark.asyncio
async def test_google_register_rejects_without_required_terms(client: AsyncClient):
    """필수 약관 미동의 → 에러."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=_make_pending(google_id="google-sub-3333"))

    with patch("app.api.google_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/google/register",
            json={
                **_REGISTER_BASE,
                "email": "terms@test.com",
                "nickname": "약관거부",
                "terms_of_service": False,
            },
        )

    body = resp.json()
    assert body["success"] is False
    assert "약관" in body["error"]


@pytest.mark.asyncio
async def test_google_register_rejects_duplicate_email(client: AsyncClient):
    """register 시점 이메일 중복 재확인 (race condition 방지)."""
    await User.create(email="dup@test.com", nickname="기존유저", name="기존", password_hash="pw")

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=_make_pending(google_id="google-sub-2222", email=""))
    mock_redis.delete = AsyncMock()

    with patch("app.api.google_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/google/register",
            json={**_REGISTER_BASE, "registration_token": "tok4", "email": "dup@test.com", "nickname": "새닉"},
        )

    body = resp.json()
    assert body["success"] is False
    assert "이메일" in body["error"]
