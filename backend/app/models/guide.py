from tortoise import fields
from tortoise.models import Model


class Guide(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="guides")
    prescription = fields.ForeignKeyField("models.Prescription", related_name="guides")
    content = fields.JSONField()  # structured guide content from LLM
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guides"
