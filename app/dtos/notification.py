from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class NotificationType(str, Enum):
    MEDICATION = "MEDICATION"
    CARE = "CARE"
    CHAT = "CHAT"
    SYSTEM = "SYSTEM"


class NotificationItem(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    notification_id: Annotated[str, Field(alias="id")]
    type: NotificationType
    is_read: bool
    title: str | None = None
    content: str | None = None


class NotificationListResponse(BaseModel):
    notifications: list[NotificationItem]
