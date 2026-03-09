import pytest
from httpx import AsyncClient

from app.models.patient_profile import PatientProfile
from app.models.user import User

_BASE_SIGNUP = {
    "email": "patient@test.com",
    "password": "Pass1234!",
    "nickname": "환자닉",
    "name": "환자",
    "terms_of_service": True,
    "privacy_policy": True,
}


@pytest.mark.asyncio
async def test_patient_signup_creates_profile(client: AsyncClient):
    resp = await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "role": "PATIENT"})
    assert resp.json()["success"] is True
    user = await User.get(email=_BASE_SIGNUP["email"])
    profile = await PatientProfile.get_or_none(user=user)
    assert profile is not None


@pytest.mark.asyncio
async def test_guardian_signup_has_no_profile(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={**_BASE_SIGNUP, "email": "guardian@test.com", "nickname": "보호자닉", "role": "GUARDIAN"},
    )
    assert resp.json()["success"] is True
    user = await User.get(email="guardian@test.com")
    profile = await PatientProfile.get_or_none(user=user)
    assert profile is None


@pytest.mark.asyncio
async def test_get_me_returns_patient_profile(client: AsyncClient):
    await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "role": "PATIENT"})
    login_resp = await client.post("/api/auth/login", json={"email": _BASE_SIGNUP["email"], "password": _BASE_SIGNUP["password"]})
    token = login_resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.get("/api/users/me")
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["patient_profile"] is not None
    assert body["data"]["patient_profile"]["height_cm"] is None


@pytest.mark.asyncio
async def test_update_patient_profile(client: AsyncClient):
    await client.post("/api/auth/signup", json={**_BASE_SIGNUP, "role": "PATIENT"})
    login_resp = await client.post("/api/auth/login", json={"email": _BASE_SIGNUP["email"], "password": _BASE_SIGNUP["password"]})
    token = login_resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.patch("/api/users/me", json={"height_cm": 170.5, "weight_kg": 65.0})
    assert resp.json()["success"] is True

    me_resp = await client.get("/api/users/me")
    profile = me_resp.json()["data"]["patient_profile"]
    assert profile["height_cm"] == 170.5
    assert profile["weight_kg"] == 65.0
