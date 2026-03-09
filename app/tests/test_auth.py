import pytest
from httpx import AsyncClient

from app.models.auth_provider import AuthProvider
from app.models.terms_consent import TermsConsent
from app.models.user import User

_BASE_SIGNUP = {
    "email": "user@test.com",
    "nickname": "닉네임",
    "name": "테스트",
    "terms_of_service": True,
    "privacy_policy": True,
}


@pytest.mark.asyncio
async def test_signup_creates_local_auth_provider(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={
            "email": "new@test.com",
            "password": "Pass1234!",
            "nickname": "신규유저",
            "name": "테스트",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    assert resp.json()["success"] is True
    user = await User.filter(email="new@test.com").first()
    provider = await AuthProvider.filter(user=user).first()
    assert provider is not None
    assert provider.provider == "LOCAL"
    assert provider.provider_user_id == "new@test.com"


@pytest.mark.asyncio
async def test_signup_rejects_without_required_terms(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={
            "email": "user@test.com",
            "password": "Pass1234!",
            "nickname": "닉네임",
            "name": "테스트",
            "terms_of_service": False,
            "privacy_policy": True,
        },
    )
    body = resp.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_signup_stores_marketing_consent(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={
            "email": "user@test.com",
            "password": "Pass1234!",
            "nickname": "닉네임",
            "name": "테스트",
            "terms_of_service": True,
            "privacy_policy": True,
            "marketing_consent": True,
        },
    )
    assert resp.json()["success"] is True
    user = await User.filter(email="user@test.com").first()
    consent = await TermsConsent.filter(user=user).first()
    assert consent is not None
    assert consent.marketing_consent is True


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_pw", [
    "short1!",    # 7자 — 길이 부족
    "abcdefgh",   # 1종 (소문자만)
    "abcdef12",   # 2종 (소문자 + 숫자)
    "ABCDEF12",   # 2종 (대문자 + 숫자)
    "abcdABCD",   # 2종 (소문자 + 대문자)
])
async def test_signup_rejects_weak_password(client: AsyncClient, bad_pw: str):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": bad_pw})
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("good_pw", [
    "abcdef1!",   # 3종 (소문자 + 숫자 + 특수)
    "Abcdefg1",   # 3종 (대소문자 + 숫자)
    "ABCDEF1!",   # 3종 (대문자 + 숫자 + 특수)
])
async def test_signup_accepts_valid_password(client: AsyncClient, good_pw: str):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": good_pw})
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_signup_rejects_duplicate_nickname(client: AsyncClient):
    base = {
        "password": "Pass1234!",
        "name": "테스트",
        "terms_of_service": True,
        "privacy_policy": True,
    }
    await client.post("/api/auth/signup", json={**base, "email": "a@test.com", "nickname": "동일닉"})
    resp = await client.post("/api/auth/signup", json={**base, "email": "b@test.com", "nickname": "동일닉"})
    body = resp.json()
    assert body["success"] is False
    assert "닉네임" in body["error"]
