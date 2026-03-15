from unittest.mock import patch

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


class FakeRedis:
    """테스트용 in-memory Redis mock."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        if key in self._store:
            del self._store[key]
            return 1
        return 0


_fake_redis = FakeRedis()


@pytest.fixture(autouse=True)
def mock_state_redis():
    async def _get_fake():
        return _fake_redis

    with patch("app.services.invite_service.get_state_redis", side_effect=_get_fake):
        yield
    _fake_redis._store.clear()


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["data"]["access_token"]


# ──────────────────────────────────────────────
# Phase 1: 초대 토큰 생성
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patient_creates_invite_token(client: AsyncClient):
    """환자가 초대 토큰을 생성하면 token과 invite_url이 반환된다."""
    await client.post("/api/auth/signup", json=_PATIENT)
    token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.post("/api/caregivers/invite")
    body = resp.json()
    assert resp.status_code == 200
    assert body["success"] is True
    assert "token" in body["data"]
    assert "invite_url" in body["data"]


@pytest.mark.asyncio
async def test_guardian_creates_invite_token(client: AsyncClient):
    """보호자도 역방향 초대 토큰을 생성할 수 있다."""
    await client.post("/api/auth/signup", json=_GUARDIAN)
    token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.post("/api/caregivers/invite")
    body = resp.json()
    assert resp.status_code == 200
    assert body["success"] is True
    assert "token" in body["data"]


# ──────────────────────────────────────────────
# Phase 2: 토큰 검증
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invite_token_validates_successfully(client: AsyncClient):
    """유효한 토큰 조회 시 초대자 정보가 반환된다."""
    await client.post("/api/auth/signup", json=_PATIENT)
    token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {token}"

    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]

    resp = await client.get(f"/api/caregivers/invite/{invite_token}")
    body = resp.json()
    assert resp.status_code == 200
    assert body["data"]["inviter_name"] == _PATIENT["name"]
    assert body["data"]["inviter_role"] == "PATIENT"


@pytest.mark.asyncio
async def test_expired_invite_token_rejected(client: AsyncClient):
    """존재하지 않는/만료된 토큰 → 404."""
    await client.post("/api/auth/signup", json=_PATIENT)
    token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.get("/api/caregivers/invite/nonexistent-token-abc")
    assert resp.status_code == 404


# ──────────────────────────────────────────────
# Phase 3: 토큰 수락 (role 교차 검증 포함)
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_accept_invite_creates_approved_mapping(client: AsyncClient):
    """PATIENT 초대 + GUARDIAN 수락 → APPROVED 상태의 mapping이 즉시 생성된다."""
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {patient_token}"
    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]

    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.post(f"/api/caregivers/invite/{invite_token}/accept")
    body = resp.json()
    assert resp.status_code == 200
    assert body["success"] is True
    assert body["data"]["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_accept_invite_token_consumed(client: AsyncClient):
    """수락 후 같은 토큰을 다시 사용하면 404 실패한다."""
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {patient_token}"
    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]

    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    await client.post(f"/api/caregivers/invite/{invite_token}/accept")

    resp = await client.post(f"/api/caregivers/invite/{invite_token}/accept")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_self_invite_rejected(client: AsyncClient):
    """자기 자신의 초대 토큰을 수락할 수 없다."""
    await client.post("/api/auth/signup", json=_PATIENT)
    token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {token}"

    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]

    resp = await client.post(f"/api/caregivers/invite/{invite_token}/accept")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_wrong_role_accept_rejected(client: AsyncClient):
    """PATIENT이 만든 초대를 다른 PATIENT이 수락하면 403 거부된다."""
    patient2 = {**_PATIENT, "email": "patient2@test.com", "nickname": "환자2닉"}
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=patient2)

    token1 = await _login(client, _PATIENT["email"], _PATIENT["password"])
    client.headers["Authorization"] = f"Bearer {token1}"
    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]

    token2 = await _login(client, patient2["email"], patient2["password"])
    client.headers["Authorization"] = f"Bearer {token2}"
    resp = await client.post(f"/api/caregivers/invite/{invite_token}/accept")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_duplicate_mapping_on_accept_rejected(client: AsyncClient):
    """이미 APPROVED 연결이 존재하면 토큰 수락 시 409 충돌."""
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])

    # 첫 번째 초대 + 수락
    client.headers["Authorization"] = f"Bearer {patient_token}"
    create_resp1 = await client.post("/api/caregivers/invite")
    invite_token1 = create_resp1.json()["data"]["token"]
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    await client.post(f"/api/caregivers/invite/{invite_token1}/accept")

    # 두 번째 초대 + 수락 시도
    client.headers["Authorization"] = f"Bearer {patient_token}"
    create_resp2 = await client.post("/api/caregivers/invite")
    invite_token2 = create_resp2.json()["data"]["token"]
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.post(f"/api/caregivers/invite/{invite_token2}/accept")
    assert resp.status_code == 409


# ──────────────────────────────────────────────
# DELETE / GET 기존 엔드포인트 유지 검증
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_revoke_approved_mapping(client: AsyncClient):
    """APPROVED 연결을 REVOKED로 해제할 수 있다."""
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])

    client.headers["Authorization"] = f"Bearer {patient_token}"
    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    accept_resp = await client.post(f"/api/caregivers/invite/{invite_token}/accept")
    mapping_id = accept_resp.json()["data"]["id"]

    resp = await client.delete(f"/api/caregivers/{mapping_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["message"] == "연결이 해제되었습니다."


@pytest.mark.asyncio
async def test_list_patients_and_caregivers(client: AsyncClient):
    """보호자는 관리 환자 목록, 환자는 보호자 목록을 조회할 수 있다."""
    await client.post("/api/auth/signup", json=_PATIENT)
    await client.post("/api/auth/signup", json=_GUARDIAN)

    patient_token = await _login(client, _PATIENT["email"], _PATIENT["password"])
    guardian_token = await _login(client, _GUARDIAN["email"], _GUARDIAN["password"])

    # 초대 → 수락으로 연결 생성
    client.headers["Authorization"] = f"Bearer {patient_token}"
    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    await client.post(f"/api/caregivers/invite/{invite_token}/accept")

    # 보호자 → 환자 목록 조회
    resp = await client.get("/api/caregivers/patients")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    # 환자 → 보호자 목록 조회
    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.get("/api/caregivers/my-caregivers")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
