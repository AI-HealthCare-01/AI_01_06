from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from app import config

_SIGNUP = {
    "email": "sec@test.com",
    "password": "Pass1234!",
    "nickname": "보안테스트",
    "name": "테스트",
    "role": "PATIENT",
    "terms_of_service": True,
    "privacy_policy": True,
}


@pytest.mark.asyncio
async def test_logout_blacklists_token(client: AsyncClient):
    """로그아웃 후 동일 access token으로 API 호출 → 401."""
    await client.post("/api/auth/signup", json=_SIGNUP)
    login_resp = await client.post("/api/auth/login", json={"email": _SIGNUP["email"], "password": _SIGNUP["password"]})
    token = login_resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    logout_resp = await client.post("/api/auth/logout")
    assert logout_resp.json()["success"] is True

    me_resp = await client.get("/api/users/me")
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_still_works(client: AsyncClient):
    """로그아웃하지 않은 토큰은 정상 동작."""
    await client.post("/api/auth/signup", json=_SIGNUP)
    login_resp = await client.post("/api/auth/login", json={"email": _SIGNUP["email"], "password": _SIGNUP["password"]})
    token = login_resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    me_resp = await client.get("/api/users/me")
    assert me_resp.status_code == 200


@pytest.mark.asyncio
async def test_token_without_jti_bypasses_blacklist(client: AsyncClient):
    """jti 없는 기존 형식 토큰도 정상 동작 (하위 호환)."""
    await client.post("/api/auth/signup", json=_SIGNUP)

    # jti 없는 구형 토큰 직접 생성
    payload = {"sub": "1", "role": "PATIENT", "exp": datetime.now(UTC) + timedelta(minutes=60), "type": "access"}
    old_token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)
    client.headers["Authorization"] = f"Bearer {old_token}"

    me_resp = await client.get("/api/users/me")
    assert me_resp.status_code == 200
