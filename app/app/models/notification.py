from tortoise import fields
from tortoise.models import Model


class NotificationSetting(Model):
    user = fields.OneToOneField("models.User", related_name="notification_setting", primary_key=True)
    medication_enabled = fields.BooleanField(default=True)
    caregiver_enabled = fields.BooleanField(default=True)
    time_format = fields.CharField(max_length=10, null=True)  # 12H | 24H
    sound_key = fields.CharField(max_length=50, null=True)
    morning_time = fields.CharField(max_length=8, null=True)  # "HH:MM" 형식
    noon_time = fields.CharField(max_length=8, null=True)
    evening_time = fields.CharField(max_length=8, null=True)
    bedtime_time = fields.CharField(max_length=8, null=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "notification_settings"


class Notification(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="notifications")
    notification_type = fields.CharField(max_length=50)  # MEDICATION | CAREGIVER | SYSTEM
    title = fields.CharField(max_length=255, null=True)
    body = fields.TextField(null=True)
    is_read = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    read_at = fields.DatetimeField(null=True)

    class Meta:
        table = "notifications"
        indexes = [("user_id", "is_read")]
