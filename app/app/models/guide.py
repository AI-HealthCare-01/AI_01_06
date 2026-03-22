from tortoise import fields
from tortoise.models import Model


class Guide(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    acted_by = fields.ForeignKeyField("models.User", null=True, related_name="proxy_guides")
    prescription = fields.ForeignKeyField("models.Prescription", related_name="guides")
    content = fields.JSONField(null=True)  # structured guide content from LLM
    status = fields.CharField(max_length=20, default="generating")
    created_at = fields.DatetimeField(auto_now_add=True)
    profile_snapshot_at = fields.DatetimeField(null=True)

    class Meta:
        table = "guides"
