import pytest
from httpx import AsyncClient

from app.models.notification import Notification
from app.models.user import User
from app.services.notification_service import create_notification


@pytest.mark.asyncio
async def test_create_and_list_notifications(auth_client: AsyncClient):
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]
    user = await User.get(id=user_id)
    await Notification.create(user=user, notification_type="SYSTEM", title="테스트", body="내용")

    resp = await auth_client.get("/api/notifications")
    assert resp.json()["success"] is True
    assert len(resp.json()["data"]) == 1
    assert resp.json()["data"][0]["title"] == "테스트"


@pytest.mark.asyncio
async def test_mark_notification_read(auth_client: AsyncClient):
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]
    user = await User.get(id=user_id)
    notif = await Notification.create(user=user, notification_type="MEDICATION", title="복약 알림")

    resp = await auth_client.patch(f"/api/notifications/{notif.id}/read")
    assert resp.json()["success"] is True
    assert resp.json()["data"]["is_read"] is True

    await notif.refresh_from_db()
    assert notif.read_at is not None


@pytest.mark.asyncio
async def test_update_notification_settings(auth_client: AsyncClient):
    resp = await auth_client.put(
        "/api/notifications/settings",
        json={"time_format": "24H", "morning_time": "08:00:00"},
    )
    assert resp.json()["success"] is True

    settings_resp = await auth_client.get("/api/notifications/settings")
    assert settings_resp.json()["data"]["time_format"] == "24H"


@pytest.mark.asyncio
async def test_unread_count(auth_client: AsyncClient):
    """읽지 않은 알림 카운트 API 검증."""
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]
    user = await User.get(id=user_id)

    await Notification.create(user=user, notification_type="SYSTEM", title="알림1")
    await Notification.create(user=user, notification_type="SYSTEM", title="알림2", is_read=True)

    resp = await auth_client.get("/api/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] == 1


@pytest.mark.asyncio
async def test_read_all_notifications(auth_client: AsyncClient):
    """일괄 읽음 처리 API 검증."""
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]
    user = await User.get(id=user_id)

    await Notification.create(user=user, notification_type="SYSTEM", title="알림1")
    await Notification.create(user=user, notification_type="SYSTEM", title="알림2")

    resp = await auth_client.post("/api/notifications/read-all")
    assert resp.status_code == 200
    assert resp.json()["data"]["updated_count"] == 2

    count_resp = await auth_client.get("/api/notifications/unread-count")
    assert count_resp.json()["data"]["count"] == 0


@pytest.mark.asyncio
async def test_create_notification_respects_setting(auth_client: AsyncClient):
    """알림 생성 시 enabled 설정을 확인하여 disabled면 생성하지 않음."""
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]
    user = await User.get(id=user_id)

    await auth_client.put(
        "/api/notifications/settings",
        json={"medication_enabled": False},
    )

    result = await create_notification(user.id, "MEDICATION", "복약 알림", "아침 약 복용 시간")
    assert result is None

    result2 = await create_notification(user.id, "CAREGIVER", "보호자 알림", "연결 수락")
    assert result2 is not None
    assert result2.notification_type == "CAREGIVER"


@pytest.mark.asyncio
async def test_create_notification_no_setting(auth_client: AsyncClient):
    """NotificationSetting 레코드가 없으면 기본 enabled로 알림 생성."""
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]

    result = await create_notification(user_id, "MEDICATION", "복약 알림", "테스트")
    assert result is not None


@pytest.mark.asyncio
async def test_create_notification_invalid_type(auth_client: AsyncClient):
    """허용되지 않은 notification_type은 ValueError를 발생시킨다."""
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]

    with pytest.raises(ValueError, match="허용되지 않은 알림 유형"):
        await create_notification(user_id, "INVALID_TYPE", "잘못된 알림", "테스트")


@pytest.mark.asyncio
async def test_settings_with_enabled_fields(auth_client: AsyncClient):
    """알림 설정 PUT/GET에서 새 필드 라운드트립 검증."""
    await auth_client.put(
        "/api/notifications/settings",
        json={"medication_enabled": False, "caregiver_enabled": True, "morning_time": "07:30"},
    )
    resp = await auth_client.get("/api/notifications/settings")
    data = resp.json()["data"]
    assert data["medication_enabled"] is False
    assert data["caregiver_enabled"] is True
    assert data["morning_time"] == "07:30"
