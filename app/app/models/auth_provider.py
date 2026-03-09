from tortoise import fields
from tortoise.models import Model


class AuthProvider(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="auth_providers")
    provider = fields.CharField(max_length=30)
    provider_user_id = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "auth_providers"
        unique_together = (("provider", "provider_user_id"),)
