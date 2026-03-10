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
@pytest.mark.parametrize(
    "bad_pw",
    [
        "short1!",  # 7자 — 길이 부족
        "abcdefgh",  # 1종 (소문자만)
        "abcdef12",  # 2종 (소문자 + 숫자)
        "ABCDEF12",  # 2종 (대문자 + 숫자)
        "abcdABCD",  # 2종 (소문자 + 대문자)
    ],
)
async def test_signup_rejects_weak_password(client: AsyncClient, bad_pw: str):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": bad_pw})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_accepts_valid_password(client: AsyncClient):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Abcdefg1"})
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_signup_role_defaults_to_patient_uppercase(client: AsyncClient):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Pass1234!"})
    assert resp.json()["data"]["role"] == "PATIENT"


@pytest.mark.asyncio
async def test_signup_guardian_role_stored_uppercase(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={**_BASE_SIGNUP, "email": "guardian@test.com", "nickname": "보호자닉", "password": "Pass1234!", "role": "GUARDIAN"},
    )
    assert resp.json()["data"]["role"] == "GUARDIAN"


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


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_role", ["patient", "guardian", "Patient", "Guardian", "ADMIN", "USER"])
async def test_signup_rejects_invalid_role(client: AsyncClient, bad_role: str):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Pass1234!", "role": bad_role})
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_gender", ["male", "female", "Male", "OTHER"])
async def test_signup_rejects_invalid_gender(client: AsyncClient, bad_gender: str):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Pass1234!", "gender": bad_gender})
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("good_gender", ["M", "F", None])
async def test_signup_accepts_valid_gender(client: AsyncClient, good_gender: str | None):
    unique_email = f"gender_{good_gender or 'none'}@test.com"
    unique_nick = f"닉_{good_gender or 'none'}"
    resp = await client.post(
        "/api/auth/signup",
        json={**_BASE_SIGNUP, "email": unique_email, "nickname": unique_nick, "password": "Pass1234!", "gender": good_gender},
    )
    assert resp.json()["success"] is True
    user = await User.filter(email=unique_email).first()
    assert user.gender == good_gender


@pytest.mark.asyncio
async def test_login_success_returns_tokens(client: AsyncClient):
    await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Pass1234!"})
    resp = await client.post("/api/auth/login", json={"email": _BASE_SIGNUP["email"], "password": "Pass1234!"})
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_fails_with_wrong_password(client: AsyncClient):
    await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Pass1234!"})
    resp = await client.post("/api/auth/login", json={"email": _BASE_SIGNUP["email"], "password": "Wrong1234!"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_fails_with_unknown_email(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "Pass1234!"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(client: AsyncClient):
    await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Pass1234!"})
    login_resp = await client.post("/api/auth/login", json={"email": _BASE_SIGNUP["email"], "password": "Pass1234!"})
    refresh_token = login_resp.json()["data"]["refresh_token"]

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]


@pytest.mark.asyncio
async def test_logout_requires_authentication(auth_client: AsyncClient):
    resp = await auth_client.post("/api/auth/logout")
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_login_locks_account_after_max_attempts(client: AsyncClient):
    await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "password": "Pass1234!"})
    for _ in range(5):
        await client.post("/api/auth/login", json={"email": _BASE_SIGNUP["email"], "password": "Wrong1234!"})

    resp = await client.post("/api/auth/login", json={"email": _BASE_SIGNUP["email"], "password": "Pass1234!"})
    assert resp.status_code == 401
