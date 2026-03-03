"""
notifications 도메인 Tortoise ORM 모델 (CharEnumField 적용).

기준: docs/dev/Sullivan_Init.sql
포함 테이블:
  - notification_settings
  - notifications
"""

import uuid

from tortoise import fields, models

from app.core.enums import NotificationType
from app.models.users import User


class NotificationSetting(models.Model):
    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User", pk=True, related_name="notification_settings"
    )
    time_format = fields.CharField(max_length=10, null=True)
    sound_key = fields.CharField(max_length=50, null=True)
    morning_time = fields.TimeField(null=True)
    noon_time = fields.TimeField(null=True)
    evening_time = fields.TimeField(null=True)
    bedtime_time = fields.TimeField(null=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "notification_settings"


class Notification(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="notifications"
    )
    type = fields.CharEnumField(NotificationType, max_length=50)
    title = fields.CharField(max_length=255, null=True)
    body = fields.TextField(null=True)
    is_read = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    read_at = fields.DatetimeField(null=True)

    class Meta:
        table = "notifications"
