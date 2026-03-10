from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(primary_key=True)
    email = fields.CharField(max_length=255, unique=True)
    nickname = fields.CharField(max_length=100, unique=True)
    password_hash = fields.CharField(max_length=255, null=True)
    name = fields.CharField(max_length=100)
    role = fields.CharField(max_length=20, default="PATIENT")  # PATIENT | GUARDIAN
    birth_date = fields.DateField(null=True)
    gender = fields.CharField(max_length=10, null=True)
    phone = fields.CharField(max_length=20, null=True)
    font_size_mode = fields.CharField(max_length=20, null=True)  # SMALL | LARGE
    failed_login_attempts = fields.IntField(default=0)
    locked_until = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "users"
