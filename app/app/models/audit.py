from tortoise import fields
from tortoise.models import Model


class AuditLog(Model):
    id = fields.IntField(primary_key=True)
    actor = fields.ForeignKeyField("models.User", related_name="audit_logs")
    action_type = fields.CharField(max_length=100)  # LOGIN | SIGNUP | PRESCRIPTION_UPLOAD | ...
    resource_type = fields.CharField(max_length=50, null=True)
    resource_id = fields.CharField(max_length=255, null=True)
    ip_address = fields.CharField(max_length=45)
    outcome = fields.CharField(max_length=20, null=True)  # SUCCESS | FAILURE
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"
