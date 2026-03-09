from tortoise import fields
from tortoise.models import Model


class CaregiverPatientMapping(Model):
    id = fields.IntField(primary_key=True)
    caregiver = fields.ForeignKeyField("models.User", related_name="managed_patients")
    patient = fields.ForeignKeyField("models.User", related_name="assigned_caregivers")
    status = fields.CharField(max_length=20, default="PENDING")  # PENDING|APPROVED|REJECTED|REVOKED
    requested_at = fields.DatetimeField(auto_now_add=True)
    accepted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "caregiver_patient_mappings"
        unique_together = (("caregiver", "patient"),)
