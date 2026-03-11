from tortoise import fields
from tortoise.models import Model


class DrugDocument(Model):
    id = fields.IntField(primary_key=True)
    drug_name = fields.CharField(max_length=200, index=True)
    drug_name_en = fields.CharField(max_length=200, null=True)
    section = fields.CharField(max_length=50)
    content = fields.TextField()
    source = fields.CharField(max_length=100, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "drug_documents"
        unique_together = (("drug_name", "section"),)
