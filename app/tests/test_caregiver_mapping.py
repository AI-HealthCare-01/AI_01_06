import pytest
from httpx import AsyncClient

_PATIENT = {
    "email": "patient@test.com",
    "password": "Pass1234!",
    "nickname": "환자닉",
    "name": "환자",
    "role": "PATIENT",
    "terms_of_service": True,
    "privacy_policy": True,
}
_GUARDIAN = {
    "email": "guardian@test.com",
    "password": "Pass1234!",
    "nickname": "보호자닉",
    "name": "보호자",
    "role": "GUARDIAN",
    "terms_of_service": True,
    "privacy_policy": True,
}


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_guardian_requests_patient_link(client: AsyncClient):
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)
    token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.post("/api/caregivers/request", json={"patient_nickname": "환자닉"})
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_patient_approves_request(client: AsyncClient):
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    req_resp = await client.post("/api/caregivers/request", json={"patient_nickname": "환자닉"})
    mapping_id = req_resp.json()["data"]["id"]

    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.patch(f"/api/caregivers/requests/{mapping_id}", json={"status": "APPROVED"})
    assert resp.json()["data"]["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_patient_rejects_request(client: AsyncClient):
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    req_resp = await client.post("/api/caregivers/request", json={"patient_nickname": "환자닉"})
    mapping_id = req_resp.json()["data"]["id"]

    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.patch(f"/api/caregivers/requests/{mapping_id}", json={"status": "REJECTED"})
    assert resp.json()["data"]["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_duplicate_request_rejected(client: AsyncClient):
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    await client.post("/api/caregivers/request", json={"patient_nickname": "환자닉"})
    resp = await client.post("/api/caregivers/request", json={"patient_nickname": "환자닉"})
    assert resp.json()["success"] is False


@pytest.mark.asyncio
async def test_patient_cannot_request(client: AsyncClient):
    await client.post("/api/auth/signup", json=_PATIENT)
    token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.post("/api/caregivers/request", json={"patient_nickname": "환자닉"})
    assert resp.status_code == 403
