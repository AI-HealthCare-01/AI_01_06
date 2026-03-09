from tortoise import fields
from tortoise.models import Model


class AuthProvider(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="auth_providers")
    provider = fields.CharField(max_length=30)  # LOCAL | KAKAO | NAVER | GOOGLE
    provider_user_id = fields.CharField(max_length=255)
    # TODO: 소셜 로그인 구현 시 access_token/refresh_token을 암호화(AES-256 또는 Fernet) 저장으로 변경할 것
    access_token = fields.TextField(null=True)
    refresh_token = fields.TextField(null=True)
    token_expires_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "auth_providers"
        unique_together = (("provider", "provider_user_id"),)
