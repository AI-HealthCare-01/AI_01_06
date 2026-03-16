from unittest.mock import patch

import pytest
from httpx import AsyncClient

_PATIENT = {
    "email": "patient@test.com",
    "password": "Pass1234!",
    "nickname": "환자닉",
    "name": "홍길동",
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


@pytest.fixture(autouse=True)
def mock_state_redis(fake_redis_cleanup):
    async def _get_fake():
        return fake_redis_cleanup

    with patch("app.services.invite_service.get_state_redis", side_effect=_get_fake):
        yield


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["data"]["access_token"]


async def _create_linked_pair(client: AsyncClient) -> tuple[str, str, int]:
    """환자+보호자 생성 → 초대 → 수락 → (patient_token, guardian_token, patient_id)."""
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)
    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])

    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.post("/api/caregivers/invite")
    invite_token = resp.json()["data"]["token"]
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    await client.post(f"/api/caregivers/invite/{invite_token}/accept")

    resp = await client.get("/api/caregivers/patients")
    patient_id = resp.json()["data"][0]["id"]
    return patient_token, guardian_token, patient_id


@pytest.mark.asyncio
async def test_guardian_views_patient_schedules(client: AsyncClient):
    """보호자가 연결된 환자의 오늘 스케줄을 조회할 수 있다."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get("/api/schedules/today", headers={"X-Acting-For": str(patient_id)})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_guardian_cannot_access_unlinked_patient(client: AsyncClient):
    """미연결 환자 데이터 접근 시 403."""
    _, guardian_token, _ = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get("/api/schedules/today", headers={"X-Acting-For": "9999"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_patient_self_access_unchanged(client: AsyncClient):
    """X-Acting-For 없이 기존 동작 유지 (회귀)."""
    patient_token, _, _ = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.get("/api/schedules/today")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_patient_cannot_use_acting_for_header(client: AsyncClient):
    """PATIENT가 X-Acting-For 헤더를 보내면 403."""
    patient_token, _, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.get("/api/schedules/today", headers={"X-Acting-For": str(patient_id)})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_revoked_mapping_blocks_access(client: AsyncClient):
    """REVOKED 매핑으로 접근 불가."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get("/api/caregivers/patients")
    mapping_id = resp.json()["data"][0]["mapping_id"]
    await client.delete(f"/api/caregivers/{mapping_id}")

    resp = await client.get("/api/schedules/today", headers={"X-Acting-For": str(patient_id)})
    assert resp.status_code == 403
