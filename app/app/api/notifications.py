import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.notification import Notification, NotificationSetting
from app.models.user import User
from app.services.notification_service import check_missed_for_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")


class NotificationSettingUpdate(BaseModel):
    medication_enabled: bool | None = None
    caregiver_enabled: bool | None = None
    time_format: str | None = None
    sound_key: str | None = None
    morning_time: str | None = None
    noon_time: str | None = None
    evening_time: str | None = None
    bedtime_time: str | None = None

    @field_validator("morning_time", "noon_time", "evening_time", "bedtime_time")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is not None and not _TIME_RE.match(v):
            raise ValueError("시간은 HH:MM 형식이어야 합니다 (00:00~23:59)")
        return v


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


@router.get("/unread-count")
async def get_unread_count(user: User = Depends(get_current_user)):
    count = await Notification.filter(user=user, is_read=False).count()
    return success_response({"count": count})


@router.post("/check-missed")
async def check_missed(user: User = Depends(get_current_user)):
    """로그인 직후 호출 — 현재 사용자의 미복약 알림을 즉시 생성한다."""
    created = await check_missed_for_user(user.id)
    return success_response({"created_count": created})


@router.post("/read-all")
async def read_all(user: User = Depends(get_current_user)):
    updated_count = await Notification.filter(user=user, is_read=False).update(is_read=True, read_at=datetime.now(UTC))
    return success_response({"updated_count": updated_count})


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
            "medication_enabled": setting.medication_enabled,
            "caregiver_enabled": setting.caregiver_enabled,
            "time_format": setting.time_format,
            "sound_key": setting.sound_key,
            "morning_time": str(setting.morning_time) if setting.morning_time else None,
            "noon_time": str(setting.noon_time) if setting.noon_time else None,
            "evening_time": str(setting.evening_time) if setting.evening_time else None,
            "bedtime_time": str(setting.bedtime_time) if setting.bedtime_time else None,
        }
    )


_TIME_FIELDS_ORDERED = ["morning_time", "noon_time", "evening_time", "bedtime_time"]
_TIME_LABELS = {"morning_time": "아침", "noon_time": "점심", "evening_time": "저녁", "bedtime_time": "자기전"}
_MIN_GAP_MINUTES = 240  # 4시간


def _parse_time_minutes(time_str: str) -> int:
    """'HH:MM' → 분 단위 정수."""
    h, m = map(int, time_str.split(":")[:2])
    return h * 60 + m


@router.put("/settings")
async def update_settings(req: NotificationSettingUpdate, user: User = Depends(get_current_user)):
    setting, _ = await NotificationSetting.get_or_create(user=user)
    update_data = req.model_dump(exclude_unset=True)

    # 시간 필드가 포함된 경우 간격 검증
    time_fields_in_request = [f for f in _TIME_FIELDS_ORDERED if f in update_data]
    if time_fields_in_request:
        final_times: dict[str, str | None] = {}
        for f in _TIME_FIELDS_ORDERED:
            if f in update_data:
                final_times[f] = update_data[f]
            else:
                final_times[f] = str(getattr(setting, f)) if getattr(setting, f, None) else None

        present = [(f, final_times[f]) for f in _TIME_FIELDS_ORDERED if final_times[f]]
        for i in range(len(present) - 1):
            curr_field, curr_val = present[i]
            next_field, next_val = present[i + 1]
            gap = _parse_time_minutes(str(next_val)) - _parse_time_minutes(str(curr_val))
            if gap < _MIN_GAP_MINUTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{_TIME_LABELS[curr_field]}과 {_TIME_LABELS[next_field]} 사이 간격은 최소 4시간이어야 합니다.",
                )

    for field, value in update_data.items():
        setattr(setting, field, value)
    await setting.save()
    return success_response({"message": "알림 설정이 저장되었습니다."})
