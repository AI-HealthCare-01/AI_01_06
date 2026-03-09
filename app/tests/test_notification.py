import pytest
from httpx import AsyncClient

from app.models.notification import Notification


@pytest.mark.asyncio
async def test_create_and_list_notifications(auth_client: AsyncClient):
    user_resp = await auth_client.get("/api/users/me")
    user_id = user_resp.json()["data"]["id"]

    from app.models.user import User
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

    from app.models.user import User
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
