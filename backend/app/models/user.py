from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(primary_key=True)
    email = fields.CharField(max_length=255, unique=True)
    nickname = fields.CharField(max_length=100)
    password_hash = fields.CharField(max_length=255)
    name = fields.CharField(max_length=100)
    role = fields.CharField(max_length=20, default="patient")  # patient, caregiver
    birth_date = fields.DateField(null=True)
    gender = fields.CharField(max_length=10, null=True)
    phone = fields.CharField(max_length=20, null=True)
    height = fields.FloatField(null=True)
    weight = fields.FloatField(null=True)
    allergies = fields.TextField(null=True)
    conditions = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"
