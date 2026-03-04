"""
audits 도메인 Tortoise ORM 모델 (CharEnumField 적용).

기준: docs/dev/Sullivan_Init.sql
포함 테이블:
  - audit_logs
"""

import uuid

from tortoise import fields, models

from app.core.enums import AuditOutcome
from app.models.users import User


class AuditLog(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    actor: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="audit_logs")
    action_type = fields.CharField(max_length=100)
    resource_type = fields.CharField(max_length=50, null=True)
    resource_id = fields.CharField(max_length=255, null=True)
    ip_address = fields.CharField(max_length=45)
    outcome = fields.CharEnumField(AuditOutcome, max_length=20, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"
