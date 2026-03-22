from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient

from app.models.caregiver_patient import CaregiverPatientMapping
from app.models.notification import Notification, NotificationSetting
from app.models.prescription import Medication, Prescription
from app.models.schedule import AdherenceLog, MedicationSchedule
from app.models.user import User
from app.services.notification_service import check_missed_medications

KST = ZoneInfo("Asia/Seoul")
MOCK_DATE = date(2026, 3, 18)
MOCK_NOW = datetime(2026, 3, 18, 8, 31, tzinfo=KST)


async def _create_schedule_for_user(
    user: User,
    med_name: str,
    time_of_day: str,
    target_date: date = MOCK_DATE,
) -> MedicationSchedule:
    """테스트용 스케줄 생성 헬퍼."""
    prescription = await Prescription.create(user=user, ocr_status="confirmed")
    medication = await Medication.create(prescription=prescription, name=med_name, dosage="500mg", frequency="1일 3회")
    return await MedicationSchedule.create(
        medication=medication,
        time_of_day=time_of_day,
        start_date=target_date,
        end_date=target_date,
    )


@pytest.mark.asyncio
async def test_missed_single_medication_specific_message(auth_client: AsyncClient):
    """1개 미복약 → '{시간대}, {약물명} 미복용' 형식 알림."""
    user_resp = await auth_client.get("/api/users/me")
    user = await User.get(id=user_resp.json()["data"]["id"])
    await NotificationSetting.create(user=user, morning_time="08:00")
    await _create_schedule_for_user(user, "타이레놀", "MORNING")

    fake_now = MOCK_NOW
    with patch("app.services.notification_service._now_kst", return_value=fake_now):
        await check_missed_medications()

    notifications = await Notification.filter(user=user, notification_type="MEDICATION")
    assert len(notifications) == 1
    assert "아침" in notifications[0].title
    assert "타이레놀" in notifications[0].title
    assert notifications[0].body is None


@pytest.mark.asyncio
async def test_missed_multiple_medications_generic_message(auth_client: AsyncClient):
    """2개+ 미복약 → '{시간대} 미복용' 형식 알림 (약물명 없음)."""
    user_resp = await auth_client.get("/api/users/me")
    user = await User.get(id=user_resp.json()["data"]["id"])
    await NotificationSetting.create(user=user, morning_time="08:00")
    await _create_schedule_for_user(user, "타이레놀", "MORNING")
    await _create_schedule_for_user(user, "아스피린", "MORNING")

    fake_now = MOCK_NOW
    with patch("app.services.notification_service._now_kst", return_value=fake_now):
        await check_missed_medications()

    notifications = await Notification.filter(user=user, notification_type="MEDICATION")
    assert len(notifications) == 1
    assert "아침 미복용" in notifications[0].title
    assert "타이레놀" not in notifications[0].title


@pytest.mark.asyncio
async def test_taken_medication_no_notification(auth_client: AsyncClient):
    """복약 완료 시 미복약 알림이 생성되지 않는다."""
    user_resp = await auth_client.get("/api/users/me")
    user = await User.get(id=user_resp.json()["data"]["id"])
    await NotificationSetting.create(user=user, morning_time="08:00")
    schedule = await _create_schedule_for_user(user, "타이레놀", "MORNING")

    await AdherenceLog.create(schedule=schedule, actor_user=user, target_date=MOCK_DATE, status="TAKEN")

    fake_now = MOCK_NOW
    with patch("app.services.notification_service._now_kst", return_value=fake_now):
        await check_missed_medications()

    count = await Notification.filter(user=user, notification_type="MEDICATION").count()
    assert count == 0


@pytest.mark.asyncio
async def test_missed_medication_notifies_all_caregivers(auth_client: AsyncClient, client: AsyncClient):
    """미복약 시 연결된 APPROVED 보호자 전원에게 CAREGIVER 알림 발송."""
    user_resp = await auth_client.get("/api/users/me")
    user = await User.get(id=user_resp.json()["data"]["id"])
    await NotificationSetting.create(user=user, morning_time="08:00")
    await _create_schedule_for_user(user, "타이레놀", "MORNING")

    # 보호자 2명 생성
    await client.post(
        "/api/auth/signup",
        json={
            "email": "g1@test.com",
            "password": "Test1234!",
            "nickname": "보호자1",
            "name": "김보호",
            "role": "GUARDIAN",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    g1 = await User.get(email="g1@test.com")
    await CaregiverPatientMapping.create(caregiver=g1, patient=user, status="APPROVED")

    await client.post(
        "/api/auth/signup",
        json={
            "email": "g2@test.com",
            "password": "Test1234!",
            "nickname": "보호자2",
            "name": "이보호",
            "role": "GUARDIAN",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    g2 = await User.get(email="g2@test.com")
    await CaregiverPatientMapping.create(caregiver=g2, patient=user, status="APPROVED")

    fake_now = MOCK_NOW
    with patch("app.services.notification_service._now_kst", return_value=fake_now):
        await check_missed_medications()

    g1_notis = await Notification.filter(user=g1, notification_type="CAREGIVER")
    g2_notis = await Notification.filter(user=g2, notification_type="CAREGIVER")
    assert len(g1_notis) == 1
    assert len(g2_notis) == 1
    assert user.name in g1_notis[0].title
    assert g1_notis[0].body is None
    assert g2_notis[0].body is None


@pytest.mark.asyncio
async def test_duplicate_missed_notification_prevention(auth_client: AsyncClient):
    """동일 시간대에 대해 중복 미복약 알림이 생성되지 않는다."""
    user_resp = await auth_client.get("/api/users/me")
    user = await User.get(id=user_resp.json()["data"]["id"])
    await NotificationSetting.create(user=user, morning_time="08:00")
    await _create_schedule_for_user(user, "타이레놀", "MORNING")

    fake_now = MOCK_NOW
    with patch("app.services.notification_service._now_kst", return_value=fake_now):
        await check_missed_medications()
        await check_missed_medications()  # 2회 실행

    count = await Notification.filter(user=user, notification_type="MEDICATION").count()
    assert count == 1


@pytest.mark.asyncio
async def test_medication_disabled_no_notification(auth_client: AsyncClient):
    """medication_enabled=False 시 미복약 알림이 생성되지 않는다."""
    user_resp = await auth_client.get("/api/users/me")
    user = await User.get(id=user_resp.json()["data"]["id"])
    await NotificationSetting.create(user=user, morning_time="08:00", medication_enabled=False)
    await _create_schedule_for_user(user, "타이레놀", "MORNING")

    fake_now = MOCK_NOW
    with patch("app.services.notification_service._now_kst", return_value=fake_now):
        await check_missed_medications()

    count = await Notification.filter(notification_type="MEDICATION").count()
    assert count == 0


@pytest.mark.asyncio
async def test_notification_body_not_exposed_in_api(auth_client: AsyncClient):
    """GET /api/notifications 응답에서 미복약 알림의 body가 null인지 확인."""
    user_resp = await auth_client.get("/api/users/me")
    user = await User.get(id=user_resp.json()["data"]["id"])
    await NotificationSetting.create(user=user, morning_time="08:00")
    await _create_schedule_for_user(user, "타이레놀", "MORNING")

    fake_now = MOCK_NOW
    with patch("app.services.notification_service._now_kst", return_value=fake_now):
        await check_missed_medications()

    resp = await auth_client.get("/api/notifications")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["body"] is None
