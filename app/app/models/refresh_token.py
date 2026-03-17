from tortoise import fields
from tortoise.models import Model


class RefreshToken(Model):
    id = fields.IntField(primary_key=True)
    token = fields.CharField(max_length=128, unique=True, index=True)
    user: fields.ForeignKeyRelation = fields.ForeignKeyField("models.User", related_name="refresh_tokens")
    expires_at = fields.DatetimeField()
    revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "refresh_tokens"
