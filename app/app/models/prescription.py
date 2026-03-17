from tortoise import fields
from tortoise.models import Model


class Prescription(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="prescriptions")
    hospital_name = fields.CharField(max_length=200, null=True)
    doctor_name = fields.CharField(max_length=100, null=True)
    prescription_date = fields.DateField(null=True)
    diagnosis = fields.CharField(max_length=500, null=True)
    ocr_raw = fields.JSONField(null=True)
    ocr_status = fields.CharField(max_length=20, default="pending")  # pending, completed, confirmed
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prescriptions"


class Medication(Model):
    id = fields.IntField(primary_key=True)
    prescription = fields.ForeignKeyField("models.Prescription", related_name="medications")
    name = fields.CharField(max_length=200)
    dosage = fields.CharField(max_length=100, null=True)
    frequency = fields.CharField(max_length=200, null=True)
    duration = fields.CharField(max_length=100, null=True)
    instructions = fields.TextField(null=True)

    class Meta:
        table = "medications"
