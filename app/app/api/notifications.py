from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.notification import Notification, NotificationSetting
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationSettingUpdate(BaseModel):
    time_format: str | None = None
    sound_key: str | None = None
    morning_time: str | None = None
    noon_time: str | None = None
    evening_time: str | None = None
    bedtime_time: str | None = None


@router.get("")
async def list_notifications(is_read: bool | None = None, user: User = Depends(get_current_user)):
    filters = {"user": user}
    if is_read is not None:
        filters["is_read"] = is_read
    notifications = await Notification.filter(**filters).order_by("-created_at")
    result = [
        {
            "id": n.id,
            "notification_type": n.notification_type,
            "title": n.title,
            "body": n.body,
            "is_read": n.is_read,
            "created_at": str(n.created_at),
        }
        for n in notifications
    ]
    return success_response(result)


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: int, user: User = Depends(get_current_user)):
    notification = await Notification.get_or_none(id=notification_id, user=user)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
    notification.is_read = True
    notification.read_at = datetime.now(UTC)
    await notification.save()
    return success_response({"id": notification.id, "is_read": notification.is_read})


@router.get("/settings")
async def get_settings(user: User = Depends(get_current_user)):
    setting = await NotificationSetting.get_or_none(user=user)
    if not setting:
        return success_response(None)
    return success_response(
        {
            "time_format": setting.time_format,
            "sound_key": setting.sound_key,
            "morning_time": str(setting.morning_time) if setting.morning_time else None,
            "noon_time": str(setting.noon_time) if setting.noon_time else None,
            "evening_time": str(setting.evening_time) if setting.evening_time else None,
            "bedtime_time": str(setting.bedtime_time) if setting.bedtime_time else None,
        }
    )


@router.put("/settings")
async def update_settings(req: NotificationSettingUpdate, user: User = Depends(get_current_user)):
    setting, _ = await NotificationSetting.get_or_create(user=user)
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)
    await setting.save()
    return success_response({"message": "알림 설정이 저장되었습니다."})
