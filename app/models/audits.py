from tortoise import fields, models

from app.models.users import User


class AuditLog(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    actor: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="audit_logs"
    )
    action_type = fields.CharField(max_length=100)
    resource_type = fields.CharField(max_length=50, null=True)
    resource_id = fields.CharField(max_length=255, null=True)
    ip_address = fields.CharField(max_length=45)
    outcome = fields.CharField(max_length=20, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)

    class Meta:
        table = "audit_logs"
