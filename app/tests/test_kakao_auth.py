import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.auth_provider import AuthProvider
from app.models.patient_profile import PatientProfile
from app.models.terms_consent import TermsConsent
from app.models.user import User

# ---------------------------------------------------------------------------
# Phase 1 — GET /api/auth/kakao/url
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kakao_url_returns_authorization_url(client: AsyncClient):
    """GET /api/auth/kakao/url 은 Kakao 인증 URL과 state를 반환한다."""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.get("/api/auth/kakao/url")

    body = resp.json()
    assert body["success"] is True
    assert "url" in body["data"]
    assert "kauth.kakao.com/oauth/authorize" in body["data"]["url"]
    assert "redirect_uri" in body["data"]["url"]
    assert "state" in body["data"]


# ---------------------------------------------------------------------------
# Phase 2 — POST /api/auth/kakao/callback: 기존 사용자
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kakao_callback_logs_in_existing_kakao_user(client: AsyncClient):
    """이미 Kakao로 가입한 사용자 → JWT 즉시 발급."""
    user = await User.create(email="kakao@test.com", nickname="카카오유저", name="카카오", password_hash=None)
    await AuthProvider.create(user=user, provider="KAKAO", provider_user_id="9999")
    await TermsConsent.create(user=user, terms_of_service=True, privacy_policy=True)

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "kakao_tok"}
    mock_svc.get_user_info.return_value = {
        "id": 9999,
        "kakao_account": {
            "email": "kakao@test.com",
            "profile": {"nickname": "카카오유저"},
        },
    }

    with (
        patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.kakao_auth.get_kakao_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/kakao/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "login"
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


# ---------------------------------------------------------------------------
# Phase 3 — 이메일 충돌 + 신규 사용자 (이메일 제공/미제공)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kakao_callback_rejects_email_conflict_with_local_account(client: AsyncClient):
    """LOCAL 계정과 동일 이메일로 Kakao 로그인 시도 → 에러."""
    existing = await User.create(email="conflict@test.com", nickname="기존유저", name="기존", password_hash="hashed")
    await AuthProvider.create(user=existing, provider="LOCAL", provider_user_id="conflict@test.com")

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "id": 8888,
        "kakao_account": {"email": "conflict@test.com", "profile": {"nickname": "카카오"}},
    }

    with (
        patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.kakao_auth.get_kakao_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/kakao/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is False
    assert "이메일" in body["error"]


@pytest.mark.asyncio
async def test_kakao_callback_new_user_with_email_returns_registration_token(client: AsyncClient):
    """신규 Kakao 사용자 (이메일 제공) → registration_token + 프로필 반환."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()
    mock_redis.set = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "id": 7777,
        "kakao_account": {"email": "new@kakao.com", "profile": {"nickname": "신규"}},
    }

    with (
        patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.kakao_auth.get_kakao_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/kakao/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "new_user"
    assert "registration_token" in body["data"]
    assert body["data"]["kakao_profile"]["email"] == "new@kakao.com"
    assert body["data"]["kakao_profile"]["nickname"] == "신규"


@pytest.mark.asyncio
async def test_kakao_callback_new_user_without_email_returns_empty_email(client: AsyncClient):
    """Kakao 이메일 미동의 → kakao_profile.email 이 빈 문자열."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()
    mock_redis.set = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "id": 6666,
        "kakao_account": {"profile": {"nickname": "노이메일"}},  # email 키 없음
    }

    with (
        patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.kakao_auth.get_kakao_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/kakao/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "new_user"
    assert body["data"]["kakao_profile"]["email"] == ""


# ---------------------------------------------------------------------------
# S3 — POST /api/auth/kakao/callback: state 일회용 삭제 검증
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kakao_callback_state_is_single_use(client: AsyncClient):
    """callback 처리 후 state Redis key가 삭제되는지 확인 — CSRF 일회용 보장."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()
    mock_redis.set = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "id": 11111,
        "kakao_account": {"profile": {"nickname": "테스트"}},
    }

    with (
        patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.kakao_auth.get_kakao_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/kakao/callback", json={"code": "code", "state": "one-time-state"})

    assert resp.json()["success"] is True
    # state key가 정확히 한 번, 정확한 key로 삭제됐는지 검증
    mock_redis.delete.assert_called_once_with("kakao:state:one-time-state")


# ---------------------------------------------------------------------------
# Phase 5 — POST /api/auth/kakao/register
# ---------------------------------------------------------------------------

_REGISTER_BASE = {
    "registration_token": "valid-token",
    "email": "reg@kakao.com",
    "name": "홍길동",
    "nickname": "카카오닉",
    "role": "PATIENT",
    "terms_of_service": True,
    "privacy_policy": True,
}


def _make_pending(kakao_id: str = "5555", email: str = "reg@kakao.com", nickname: str = "카카오닉") -> str:
    return json.dumps({"kakao_id": kakao_id, "kakao_email": email, "kakao_nickname": nickname})


@pytest.mark.asyncio
async def test_kakao_register_creates_user_and_returns_tokens(client: AsyncClient):
    """유효한 token + 완전한 폼 → 사용자 생성 + JWT 발급 + DB 검증."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=_make_pending())
    mock_redis.delete = AsyncMock()

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post("/api/auth/kakao/register", json=_REGISTER_BASE)

    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]

    user = await User.filter(email="reg@kakao.com").first()
    assert user is not None
    assert user.password_hash is None
    assert user.name == "홍길동"

    provider = await AuthProvider.filter(user=user, provider="KAKAO").first()
    assert provider is not None
    assert provider.provider_user_id == "5555"

    consent = await TermsConsent.filter(user=user).first()
    assert consent is not None
    assert consent.terms_of_service is True

    profile = await PatientProfile.filter(user=user).first()
    assert profile is not None  # PATIENT → PatientProfile 자동 생성


@pytest.mark.asyncio
async def test_kakao_register_with_user_entered_email_when_kakao_email_missing(client: AsyncClient):
    """Kakao 이메일 미제공 → 사용자 직접 입력 이메일로 가입."""
    pending = _make_pending(kakao_id="4444", email="", nickname="닉네임")
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=pending)
    mock_redis.delete = AsyncMock()

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/kakao/register",
            json={**_REGISTER_BASE, "registration_token": "tok2", "email": "myown@email.com", "nickname": "닉네임"},
        )

    assert resp.json()["success"] is True
    assert await User.filter(email="myown@email.com").exists()


@pytest.mark.asyncio
async def test_kakao_register_rejects_invalid_token(client: AsyncClient):
    """만료/없는 registration_token → 에러."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/kakao/register",
            json={**_REGISTER_BASE, "registration_token": "invalid"},
        )

    body = resp.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_kakao_register_rejects_without_required_terms(client: AsyncClient):
    """필수 약관 미동의 → 에러."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=_make_pending(kakao_id="3333", email="t@k.com"))

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/kakao/register",
            json={
                **_REGISTER_BASE,
                "registration_token": "tok3",
                "email": "t@k.com",
                "nickname": "닉3",
                "terms_of_service": False,
            },
        )

    body = resp.json()
    assert body["success"] is False
    assert "약관" in body["error"]


@pytest.mark.asyncio
async def test_kakao_register_rejects_duplicate_email(client: AsyncClient):
    """register 시점 이메일 중복 재확인 (race condition 방지)."""
    await User.create(email="dup@test.com", nickname="기존", name="기존", password_hash="pw")

    pending = _make_pending(kakao_id="2222", email="")
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=pending)
    mock_redis.delete = AsyncMock()

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/kakao/register",
            json={**_REGISTER_BASE, "registration_token": "tok4", "email": "dup@test.com", "nickname": "새닉"},
        )

    body = resp.json()
    assert body["success"] is False
    assert "이메일" in body["error"]


# ---------------------------------------------------------------------------
# 소프트삭제 이메일 거부 + 닉네임 sanitization
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kakao_callback_rejects_soft_deleted_email(client: AsyncClient):
    """소프트 삭제된 유저의 이메일로 Kakao 콜백 → '삭제 대기중' 에러."""
    await User.create(
        email="deleted@test.com", nickname="삭제유저", name="삭제",
        password_hash="hashed", deleted_at=datetime.now(UTC),
    )

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.delete = AsyncMock()

    mock_svc = AsyncMock()
    mock_svc.exchange_code.return_value = {"access_token": "tok"}
    mock_svc.get_user_info.return_value = {
        "id": 12345,
        "kakao_account": {"email": "deleted@test.com", "profile": {"nickname": "신규"}},
    }

    with (
        patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis),
        patch("app.api.kakao_auth.get_kakao_service", return_value=mock_svc),
    ):
        resp = await client.post("/api/auth/kakao/callback", json={"code": "code", "state": "state"})

    body = resp.json()
    assert body["success"] is False
    assert "삭제" in body["error"]


@pytest.mark.asyncio
async def test_kakao_register_rejects_soft_deleted_email(client: AsyncClient):
    """소프트 삭제된 유저의 이메일로 register → '삭제 대기중' 에러."""
    await User.create(
        email="deleted@reg.com", nickname="삭제닉", name="삭제",
        password_hash="hashed", deleted_at=datetime.now(UTC),
    )

    pending = _make_pending(kakao_id="77777", email="deleted@reg.com", nickname="새닉네임")
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=pending)
    mock_redis.delete = AsyncMock()

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/kakao/register",
            json={**_REGISTER_BASE, "email": "deleted@reg.com", "nickname": "새닉네임"},
        )

    body = resp.json()
    assert body["success"] is False
    assert "삭제" in body["error"]


@pytest.mark.asyncio
async def test_kakao_register_sanitizes_nickname(client: AsyncClient):
    """닉네임에 공백/특수문자 포함 → strip + 특수문자 제거 후 저장."""
    pending = _make_pending(kakao_id="88888", email="sanitize@test.com", nickname="테스트")
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=pending)
    mock_redis.delete = AsyncMock()

    with patch("app.api.kakao_auth.get_state_redis", return_value=mock_redis):
        resp = await client.post(
            "/api/auth/kakao/register",
            json={**_REGISTER_BASE, "email": "sanitize@test.com", "nickname": " 테스트! "},
        )

    body = resp.json()
    assert body["success"] is True
    user = await User.filter(email="sanitize@test.com").first()
    assert user.nickname == "테스트"
