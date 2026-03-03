from tortoise import fields, models

from app.models.users import User


class Notification(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="notifications"
    )
    type = fields.CharField(max_length=50)
    title = fields.CharField(max_length=255, null=True)
    body = fields.TextField(null=True)
    is_read = fields.BooleanField(default=False, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    read_at = fields.DatetimeField(null=True)

    class Meta:
        table = "notifications"


class NotificationSettings(models.Model):
    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User", pk=True, related_name="notification_settings"
    )
    time_format = fields.CharField(max_length=10, null=True)
    sound_key = fields.CharField(max_length=50, null=True)
    morning_time = fields.TimeField(null=True)
    noon_time = fields.TimeField(null=True)
    evening_time = fields.TimeField(null=True)
    bedtime_time = fields.TimeField(null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    class Meta:
        table = "notification_settings"
