from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from app import config
from app.models.refresh_token import RefreshToken

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


@pytest.mark.asyncio
async def test_refresh_with_revoked_token_rejected(client: AsyncClient):
    """revoked된 refresh token으로 갱신 시도 -> 401."""
    await client.post("/api/auth/signup", json=_SIGNUP)
    login_resp = await client.post("/api/auth/login", json={"email": _SIGNUP["email"], "password": _SIGNUP["password"]})
    refresh_token = login_resp.json()["data"]["refresh_token"]

    # DB에서 직접 revoke
    await RefreshToken.filter(token=refresh_token).update(revoked=True)

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient):
    """로그아웃 시 해당 refresh token이 DB에서 revoked 처리된다."""
    await client.post("/api/auth/signup", json=_SIGNUP)
    login_resp = await client.post("/api/auth/login", json={"email": _SIGNUP["email"], "password": _SIGNUP["password"]})
    tokens = login_resp.json()["data"]
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    await client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    rt = await RefreshToken.get_or_none(token=tokens["refresh_token"])
    assert rt is not None
    assert rt.revoked is True


@pytest.mark.asyncio
async def test_delete_account_revokes_all_tokens(client: AsyncClient):
    """회원탈퇴 시 해당 유저의 모든 refresh token이 DB에 존재하고 revoked 처리된다."""
    await client.post("/api/auth/signup", json=_SIGNUP)
    login_resp = await client.post("/api/auth/login", json={"email": _SIGNUP["email"], "password": _SIGNUP["password"]})
    tokens = login_resp.json()["data"]
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    # refresh token이 DB에 존재하는지 먼저 확인 (Red: 여기서 실패)
    rt = await RefreshToken.get_or_none(token=tokens["refresh_token"])
    assert rt is not None

    await client.request("DELETE", "/api/users/me", json={"password": _SIGNUP["password"]})

    all_tokens = await RefreshToken.filter(user_id=rt.user_id).all()
    assert len(all_tokens) > 0
    assert all(t.revoked for t in all_tokens)
