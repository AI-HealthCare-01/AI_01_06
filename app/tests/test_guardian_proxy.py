from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.chat import ChatThread
from app.models.guide import Guide
from app.models.prescription import Prescription

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


# --- 처방전 대리 접근 테스트 ---


@pytest.mark.asyncio
async def test_guardian_uploads_prescription_for_patient(client: AsyncClient):
    """보호자가 환자 대리로 처방전 업로드 → user=환자, acted_by=보호자."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    files = {"file": ("test.jpg", b"fake-image-data", "image/jpeg")}
    resp = await client.post(
        "/api/prescriptions",
        files=files,
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ocr_status"] == "processing"

    # 보호자 ID 조회
    me_resp = await client.get("/api/users/me")
    guardian_id = me_resp.json()["data"]["id"]

    # DB 검증: user=환자, acted_by=보호자
    prescription = await Prescription.get(id=data["id"])
    assert prescription.user_id == patient_id
    assert prescription.acted_by_id == guardian_id


@pytest.mark.asyncio
async def test_guardian_views_patient_prescriptions(client: AsyncClient):
    """보호자가 연결된 환자의 처방전 목록 조회."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get("/api/prescriptions", headers={"X-Acting-For": str(patient_id)})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_guardian_views_patient_ocr_result(client: AsyncClient):
    """보호자가 연결된 환자의 OCR 결과 조회."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    # 환자가 처방전 업로드
    client.headers["Authorization"] = f"Bearer {patient_token}"
    files = {"file": ("test.jpg", b"fake-image-data", "image/jpeg")}
    resp = await client.post("/api/prescriptions", files=files)
    prescription_id = resp.json()["data"]["id"]

    # 보호자가 OCR 결과 조회
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get(
        f"/api/prescriptions/{prescription_id}/ocr",
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_guardian_upload_unlinked_patient_rejected(client: AsyncClient):
    """미연결 환자에 대리 업로드 → 403."""
    _, guardian_token, _ = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    files = {"file": ("test.jpg", b"fake-image-data", "image/jpeg")}
    resp = await client.post(
        "/api/prescriptions",
        files=files,
        headers={"X-Acting-For": "9999"},
    )
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


# --- 가이드 대리 접근 테스트 ---


@pytest.mark.asyncio
async def test_guardian_creates_guide_for_patient(client: AsyncClient):
    """보호자가 환자 대리로 가이드 생성 — user=환자, acted_by=보호자, enqueue에 환자 ID 전달."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    # 환자가 처방전 업로드 (가이드 생성 전제)
    client.headers["Authorization"] = f"Bearer {patient_token}"
    files = {"file": ("test.jpg", b"fake-image-data", "image/jpeg")}
    resp = await client.post("/api/prescriptions", files=files)
    prescription_id = resp.json()["data"]["id"]

    # 보호자가 가이드 생성
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.post(
        "/api/guides",
        json={"prescription_id": prescription_id},
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 200
    guide_data = resp.json()["data"]

    # 보호자 ID 조회
    me_resp = await client.get("/api/users/me")
    guardian_id = me_resp.json()["data"]["id"]

    # DB 검증: Guide.user_id == 환자, Guide.acted_by_id == 보호자
    guide = await Guide.get(id=guide_data["id"])
    assert guide.user_id == patient_id
    assert guide.acted_by_id == guardian_id


@pytest.mark.asyncio
async def test_guardian_views_patient_guides(client: AsyncClient):
    """보호자가 연결된 환자의 가이드 목록 조회."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get("/api/guides", headers={"X-Acting-For": str(patient_id)})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_guardian_create_guide_unlinked_patient_rejected(client: AsyncClient):
    """미연결 환자에 대리 가이드 생성 → 403."""
    patient_token, guardian_token, _ = await _create_linked_pair(client)

    # 환자가 처방전 업로드
    client.headers["Authorization"] = f"Bearer {patient_token}"
    files = {"file": ("test.jpg", b"fake-image-data", "image/jpeg")}
    resp = await client.post("/api/prescriptions", files=files)
    prescription_id = resp.json()["data"]["id"]

    # 보호자가 미연결 환자 ID로 가이드 생성 시도
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.post(
        "/api/guides",
        json={"prescription_id": prescription_id},
        headers={"X-Acting-For": "9999"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_guardian_cannot_delete_patient_guide(client: AsyncClient):
    """보호자는 돌봄 대상의 가이드를 삭제할 수 없다."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    # 환자가 처방전 업로드 → 가이드 생성
    client.headers["Authorization"] = f"Bearer {patient_token}"
    files = {"file": ("test.jpg", b"fake-image-data", "image/jpeg")}
    resp = await client.post("/api/prescriptions", files=files)
    prescription_id = resp.json()["data"]["id"]

    resp = await client.post("/api/guides", json={"prescription_id": prescription_id})
    guide_id = resp.json()["data"]["id"]

    # 보호자가 대리 모드로 삭제 시도 → 403
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.delete(
        f"/api/guides/{guide_id}",
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 403


# --- 채팅 대리 접근 테스트 ---


@pytest.mark.asyncio
async def test_guardian_views_patient_chat_threads(client: AsyncClient):
    """보호자가 돌봄 대상의 상담 이력을 조회할 수 있다."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get("/api/chat/threads", headers={"X-Acting-For": str(patient_id)})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_guardian_creates_chat_for_patient(client: AsyncClient):
    """보호자 대리 상담 생성 → user=환자, acted_by=보호자."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    # 보호자 ID 조회
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    me_resp = await client.get("/api/users/me")
    guardian_id = me_resp.json()["data"]["id"]

    resp = await client.post(
        "/api/chat/threads",
        json={},
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 200

    thread_id = resp.json()["data"]["id"]
    thread = await ChatThread.get(id=thread_id)
    assert thread.user_id == patient_id
    assert thread.acted_by_id == guardian_id


@pytest.mark.asyncio
async def test_guardian_own_chat_separate(client: AsyncClient):
    """보호자 본인 상담과 대리 상담이 분리된다."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"

    # 본인 상담 생성
    resp1 = await client.post("/api/chat/threads", json={})
    assert resp1.status_code == 200

    # 대리 상담 생성
    resp2 = await client.post(
        "/api/chat/threads",
        json={},
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp2.status_code == 200

    # 본인 이력 조회 → 1개
    resp_own = await client.get("/api/chat/threads")
    assert len(resp_own.json()["data"]) == 1

    # 대리 이력 조회 → 1개
    resp_proxy = await client.get("/api/chat/threads", headers={"X-Acting-For": str(patient_id)})
    assert len(resp_proxy.json()["data"]) == 1

    # 서로 다른 thread
    assert resp_own.json()["data"][0]["id"] != resp_proxy.json()["data"][0]["id"]


@pytest.mark.asyncio
async def test_guardian_views_patient_chat_messages(client: AsyncClient):
    """보호자가 돌봄 대상의 상담 메시지를 조회할 수 있다."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"

    # 대리 상담 생성
    resp = await client.post(
        "/api/chat/threads",
        json={},
        headers={"X-Acting-For": str(patient_id)},
    )
    thread_id = resp.json()["data"]["id"]

    # 메시지 조회
    resp = await client.get(
        f"/api/chat/threads/{thread_id}/messages",
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_guardian_ends_patient_chat_thread(client: AsyncClient):
    """보호자가 대리 모드에서 상담 세션을 종료할 수 있다."""
    _, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"

    # 대리 상담 생성
    resp = await client.post(
        "/api/chat/threads",
        json={},
        headers={"X-Acting-For": str(patient_id)},
    )
    thread_id = resp.json()["data"]["id"]

    # 세션 종료
    resp = await client.patch(
        f"/api/chat/threads/{thread_id}/end",
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_patient_sees_proxy_chat_with_badge(client: AsyncClient):
    """환자가 보호자 대리 상담을 acted_by_name 포함하여 조회할 수 있다."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    # 보호자가 대리 상담 생성
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    await client.post(
        "/api/chat/threads",
        json={},
        headers={"X-Acting-For": str(patient_id)},
    )

    # 환자가 본인 상담 생성
    client.headers["Authorization"] = f"Bearer {patient_token}"
    await client.post("/api/chat/threads", json={})

    # 환자가 목록 조회 → 2개 (본인 + 대리)
    resp = await client.get("/api/chat/threads")
    data = resp.json()["data"]
    assert len(data) == 2

    # acted_by_name 확인: 대리 상담에만 보호자 이름 포함
    proxy_threads = [t for t in data if t["acted_by_name"] is not None]
    own_threads = [t for t in data if t["acted_by_name"] is None]
    assert len(proxy_threads) == 1
    assert len(own_threads) == 1
    assert proxy_threads[0]["acted_by_name"] == _GUARDIAN["name"]


# --- 프로필 대리 접근 테스트 ---


@pytest.mark.asyncio
async def test_guardian_views_patient_profile(client: AsyncClient):
    """보호자가 연결된 환자의 프로필을 조회 — 민감 정보 제외, is_proxy_view 플래그."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.get("/api/users/me", headers={"X-Acting-For": str(patient_id)})
    assert resp.status_code == 200

    data = resp.json()["data"]
    assert data["name"] == _PATIENT["name"]
    assert data["role"] == "PATIENT"
    assert data["is_proxy_view"] is True

    # 민감 정보 미포함 + 보호자 이름 포함
    sensitive_fields = {"email", "has_password", "phone"}
    assert sensitive_fields.isdisjoint(data.keys())
    assert "guardian_name" in data


@pytest.mark.asyncio
async def test_patch_me_always_updates_self_not_patient(client: AsyncClient):
    """PATCH /me는 X-Acting-For가 있어도 항상 보호자 본인만 수정한다 (환자 데이터 불변)."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    # 보호자가 X-Acting-For와 함께 PATCH → 본인 닉네임 변경
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.patch(
        "/api/users/me",
        json={"nickname": "변경된보호자"},
        headers={"X-Acting-For": str(patient_id)},
    )
    assert resp.status_code == 200

    # 보호자 본인 닉네임이 변경됨 확인
    me_resp = await client.get("/api/users/me")
    assert me_resp.json()["data"]["nickname"] == "변경된보호자"

    # 환자 닉네임은 변경되지 않음 확인
    client.headers["Authorization"] = f"Bearer {patient_token}"
    patient_resp = await client.get("/api/users/me")
    assert patient_resp.json()["data"]["nickname"] == _PATIENT["nickname"]


@pytest.mark.asyncio
async def test_delete_me_always_targets_self_not_patient(client: AsyncClient):
    """DELETE /me는 X-Acting-For가 있어도 항상 보호자 본인 계정만 삭제한다."""
    patient_token, guardian_token, patient_id = await _create_linked_pair(client)

    # 보호자가 X-Acting-For와 함께 DELETE → 본인 계정 삭제
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    resp = await client.request(
        "DELETE",
        "/api/users/me",
        headers={"X-Acting-For": str(patient_id)},
        json={"password": _GUARDIAN["password"]},
    )
    assert resp.status_code == 200

    # 환자 계정은 여전히 살아있음 확인
    client.headers["Authorization"] = f"Bearer {patient_token}"
    patient_resp = await client.get("/api/users/me")
    assert patient_resp.status_code == 200
