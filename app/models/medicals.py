from tortoise import fields, models

from app.models.users import User


class Prescription(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    patient: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="prescriptions", to_field="id"
    )
    created_by_user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="created_prescriptions", to_field="id"
    )
    hospital_name = fields.CharField(max_length=255, null=True)
    doctor_name = fields.CharField(max_length=255, null=True)
    prescription_date = fields.DateField(null=True)
    diagnosis = fields.CharField(max_length=255, null=True)
    verification_status = fields.CharField(max_length=30, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    class Meta:
        table = "prescriptions"


class PrescriptionImage(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    prescription: fields.ForeignKeyRelation[Prescription] = fields.ForeignKeyField(
        "models.Prescription", related_name="images"
    )
    file_url = fields.CharField(max_length=512)
    mime_type = fields.CharField(max_length=100, null=True)
    uploaded_at = fields.DatetimeField(auto_now_add=True, null=True)

    class Meta:
        table = "prescription_images"


class Medication(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    prescription: fields.ForeignKeyRelation[Prescription] = fields.ForeignKeyField(
        "models.Prescription", related_name="medications"
    )
    drug_name = fields.CharField(max_length=255)
    dosage = fields.CharField(max_length=100, null=True)
    frequency = fields.CharField(max_length=100, null=True)
    administration = fields.CharField(max_length=255, null=True)
    duration_days = fields.IntField(null=True)
    is_deleted = fields.BooleanField(default=False, null=True)

    class Meta:
        table = "medications"


class MedicationSchedule(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    medication: fields.ForeignKeyRelation[Medication] = fields.ForeignKeyField(
        "models.Medication", related_name="schedules"
    )
    time_of_day = fields.CharField(max_length=20)
    specific_time = fields.TimeField(null=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)

    class Meta:
        table = "medication_schedules"


class AdherenceLog(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    schedule: fields.ForeignKeyRelation[MedicationSchedule] = fields.ForeignKeyField(
        "models.MedicationSchedule", related_name="adherence_logs"
    )
    actor_user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="adherence_logs"
    )
    target_date = fields.DateField()
    status = fields.CharField(max_length=20)
    logged_at = fields.DatetimeField(auto_now_add=True, null=True)
    note = fields.TextField(null=True)

    class Meta:
        table = "adherence_logs"


class OcrJob(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    prescription_image: fields.ForeignKeyRelation[PrescriptionImage] = fields.ForeignKeyField(
        "models.PrescriptionImage", related_name="ocr_jobs"
    )
    provider = fields.CharField(max_length=50, null=True)
    status = fields.CharField(max_length=20)
    raw_ocr_json = fields.JSONField(null=True)
    extracted_text = fields.TextField(null=True)
    extracted_json = fields.JSONField(null=True)
    requested_at = fields.DatetimeField(auto_now_add=True, null=True)
    processed_at = fields.DatetimeField(null=True)

    class Meta:
        table = "ocr_jobs"
