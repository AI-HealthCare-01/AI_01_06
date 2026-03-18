from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.notification import Notification
from app.models.prescription import Medication, Prescription
from app.models.user import User

_PATIENT = {
    "email": "evt_patient@test.com",
    "password": "Pass1234!",
    "nickname": "이벤트환자",
    "name": "김환자",
    "role": "PATIENT",
    "terms_of_service": True,
    "privacy_policy": True,
}
_GUARDIAN = {
    "email": "evt_guardian@test.com",
    "password": "Pass1234!",
    "nickname": "이벤트보호자",
    "name": "박보호",
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


async def _signup_and_login(client: AsyncClient, data: dict) -> tuple[str, int]:
    """회원가입 + 로그인 후 (token, user_id)를 반환한다."""
    signup_resp = await client.post("/api/auth/signup", json=data)
    user_id = signup_resp.json()["data"]["id"]
    resp = await client.post("/api/auth/login", json={"email": data["email"], "password": data["password"]})
    token = resp.json()["data"]["access_token"]
    return token, user_id


async def _create_link(client: AsyncClient, inviter_token: str, acceptor_token: str) -> int:
    """초대 생성 + 수락 후 mapping_id를 반환한다."""
    client.headers["Authorization"] = f"Bearer {inviter_token}"
    create_resp = await client.post("/api/caregivers/invite")
    invite_token = create_resp.json()["data"]["token"]

    client.headers["Authorization"] = f"Bearer {acceptor_token}"
    accept_resp = await client.post(f"/api/caregivers/invite/{invite_token}/accept")
    return accept_resp.json()["data"]["id"]


# ──────────────────────────────────────────────
# C1/C4: 초대 수락 → 초대자에게 알림
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invite_accept_creates_notification_for_inviter(client: AsyncClient):
    """초대 수락 시 초대자에게 CAREGIVER 알림이 생성된다."""
    patient_token, patient_id = await _signup_and_login(client, _PATIENT)
    guardian_token, guardian_id = await _signup_and_login(client, _GUARDIAN)

    # 환자가 초대 → 보호자가 수락 → 환자(초대자)에게 알림
    await _create_link(client, patient_token, guardian_token)

    notifications = await Notification.filter(user_id=patient_id, notification_type="CAREGIVER")
    assert len(notifications) == 1


# ──────────────────────────────────────────────
# C3/C7: 연결 해제 → 상대방에게 알림
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_revoke_creates_notification_for_counterpart(client: AsyncClient):
    """연결 해제 시 상대방에게 CAREGIVER 알림이 생성된다."""
    patient_token, patient_id = await _signup_and_login(client, _PATIENT)
    guardian_token, guardian_id = await _signup_and_login(client, _GUARDIAN)

    mapping_id = await _create_link(client, patient_token, guardian_token)

    # 환자가 연결 해제 → 보호자에게 알림
    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.delete(f"/api/caregivers/{mapping_id}")
    assert resp.status_code == 200

    notifications = await Notification.filter(user_id=guardian_id, notification_type="CAREGIVER")
    # 수락 알림(환자에게) + 해제 알림(보호자에게) — 보호자에게는 해제 알림만
    assert len(notifications) == 1


# ──────────────────────────────────────────────
# C5: 보호자 대리 처방전/가이드
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_proxy_prescription_creates_notification(client: AsyncClient):
    """보호자가 대리로 처방전을 등록하면 환자에게 알림이 생성된다."""
    patient_token, patient_id = await _signup_and_login(client, _PATIENT)
    guardian_token, guardian_id = await _signup_and_login(client, _GUARDIAN)
    await _create_link(client, patient_token, guardian_token)

    # 보호자가 대리 처방전 등록
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    client.headers["X-Acting-For"] = str(patient_id)
    resp = await client.post(
        "/api/prescriptions",
        files={"file": ("test.png", b"fake-image-data", "image/png")},
    )
    assert resp.status_code == 200

    notifications = await Notification.filter(user_id=patient_id, notification_type="CAREGIVER")
    # 수락 알림(환자→보호자에게 갔으므로 환자 수신은 없음) + 처방전 알림 = 1
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_proxy_guide_creates_notification(client: AsyncClient):
    """보호자가 대리로 가이드를 생성하면 환자에게 알림이 생성된다."""
    patient_token, patient_id = await _signup_and_login(client, _PATIENT)
    guardian_token, guardian_id = await _signup_and_login(client, _GUARDIAN)
    await _create_link(client, patient_token, guardian_token)

    # 처방전 + OCR 완료 + 약물 데이터 준비
    patient_user = await User.get(id=patient_id)
    prescription = await Prescription.create(user=patient_user, ocr_status="ocr_completed", hospital_name="테스트병원")
    await Medication.create(prescription=prescription, name="테스트약", dosage="1정", frequency="1일 3회", duration="7일")

    # 보호자가 대리 가이드 생성
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    client.headers["X-Acting-For"] = str(patient_id)
    resp = await client.post("/api/guides", json={"prescription_id": prescription.id})
    assert resp.status_code == 200

    notifications = await Notification.filter(user_id=patient_id, notification_type="CAREGIVER")
    assert len(notifications) == 1


# ──────────────────────────────────────────────
# C6: 보호자 대리 AI상담
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_proxy_chat_creates_notification(client: AsyncClient):
    """보호자가 대리로 채팅을 생성하면 환자에게 알림이 생성된다."""
    patient_token, patient_id = await _signup_and_login(client, _PATIENT)
    guardian_token, guardian_id = await _signup_and_login(client, _GUARDIAN)
    await _create_link(client, patient_token, guardian_token)

    # 보호자가 대리 채팅 스레드 생성
    client.headers["Authorization"] = f"Bearer {guardian_token}"
    client.headers["X-Acting-For"] = str(patient_id)
    resp = await client.post("/api/chat/threads", json={})
    assert resp.status_code == 200

    notifications = await Notification.filter(user_id=patient_id, notification_type="CAREGIVER")
    assert len(notifications) == 1


# ──────────────────────────────────────────────
# 본인 모드 → 알림 미생성
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_own_mode_no_notification(client: AsyncClient):
    """본인 모드에서는 대리 알림이 생성되지 않는다."""
    patient_token, patient_id = await _signup_and_login(client, _PATIENT)

    client.headers["Authorization"] = f"Bearer {patient_token}"
    resp = await client.post(
        "/api/prescriptions",
        files={"file": ("test.png", b"fake-image-data", "image/png")},
    )
    assert resp.status_code == 200

    notifications = await Notification.filter(notification_type="CAREGIVER")
    assert len(notifications) == 0
