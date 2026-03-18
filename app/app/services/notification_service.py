from app.models.notification import Notification, NotificationSetting
from app.models.user import User

_ALLOWED_TYPES = {"MEDICATION", "CAREGIVER"}

_TYPE_SETTING_MAP: dict[str, str] = {
    "MEDICATION": "medication_enabled",
    "CAREGIVER": "caregiver_enabled",
}


async def create_notification(
    user_id: int,
    notification_type: str,
    title: str,
    body: str | None = None,
) -> Notification | None:
    """알림을 생성한다. 해당 유형이 disabled면 None을 반환한다.

    Raises:
        ValueError: 허용되지 않은 notification_type인 경우
    """
    if notification_type not in _ALLOWED_TYPES:
        raise ValueError(f"허용되지 않은 알림 유형: {notification_type}")

    setting_field = _TYPE_SETTING_MAP.get(notification_type)
    if setting_field:
        setting = await NotificationSetting.get_or_none(user_id=user_id)
        if setting and not getattr(setting, setting_field):
            return None

    user = await User.get(id=user_id)
    return await Notification.create(
        user=user,
        notification_type=notification_type,
        title=title,
        body=body,
    )
