from tortoise import fields, models

from app.models.medicals import Medication, Prescription


class MedicationGuide(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    prescription: fields.OneToOneRelation[Prescription] = fields.OneToOneField(
        "models.Prescription", related_name="guide"
    )
    guide_markdown = fields.TextField()
    precautions = fields.TextField(null=True)
    lifestyle_advice = fields.TextField(null=True)
    summary_json = fields.JSONField(null=True)
    generated_at = fields.DatetimeField(auto_now_add=True, null=True)

    class Meta:
        table = "medication_guides"


class GuideMedicationCard(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    guide: fields.ForeignKeyRelation[MedicationGuide] = fields.ForeignKeyField(
        "models.MedicationGuide", related_name="medication_cards"
    )
    medication: fields.ForeignKeyRelation[Medication] = fields.ForeignKeyField(
        "models.Medication", related_name="guide_cards"
    )
    usage_text = fields.TextField(null=True)
    warning_text = fields.TextField(null=True)

    class Meta:
        table = "guide_medication_cards"
