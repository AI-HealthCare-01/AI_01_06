"""
medicals 도메인 Tortoise ORM 모델 (CharEnumField 적용).

기준: docs/dev/Sullivan_Init.sql
포함 테이블:
  - prescriptions
  - prescription_images
  - ocr_jobs
  - medications
  - medication_schedules
  - adherence_logs
"""

import uuid

from tortoise import fields, models

from app.core.enums import (
    AdherenceStatus,
    OcrProvider,
    OcrStatus,
    TimeOfDay,
    VerificationStatus,
)
from app.models.users import User


class Prescription(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    patient: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="prescriptions")
    created_by_user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="created_prescriptions"
    )
    hospital_name = fields.CharField(max_length=255, null=True)
    doctor_name = fields.CharField(max_length=255, null=True)
    prescription_date = fields.DateField(null=True)
    diagnosis = fields.CharField(max_length=255, null=True)
    verification_status = fields.CharEnumField(VerificationStatus, max_length=30, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "prescriptions"


class PrescriptionImage(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    prescription: fields.ForeignKeyRelation[Prescription] = fields.ForeignKeyField(
        "models.Prescription", related_name="images"
    )
    file_url = fields.CharField(max_length=512)
    mime_type = fields.CharField(max_length=100, null=True)
    uploaded_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prescription_images"


class OcrJob(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    prescription_image: fields.ForeignKeyRelation[PrescriptionImage] = fields.ForeignKeyField(
        "models.PrescriptionImage", related_name="ocr_jobs"
    )
    provider = fields.CharEnumField(OcrProvider, max_length=50, null=True)
    status = fields.CharEnumField(OcrStatus, max_length=20)
    raw_ocr_json = fields.JSONField(null=True)
    extracted_text = fields.TextField(null=True)
    extracted_json = fields.JSONField(null=True)
    requested_at = fields.DatetimeField(auto_now_add=True)
    processed_at = fields.DatetimeField(null=True)

    class Meta:
        table = "ocr_jobs"


class Medication(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    prescription: fields.ForeignKeyRelation[Prescription] = fields.ForeignKeyField(
        "models.Prescription", related_name="medications"
    )
    drug_name = fields.CharField(max_length=255)
    dosage = fields.CharField(max_length=100, null=True)
    frequency = fields.CharField(max_length=100, null=True)
    administration = fields.CharField(max_length=255, null=True)
    duration_days = fields.IntField(null=True)
    is_deleted = fields.BooleanField(default=False)

    class Meta:
        table = "medications"


class MedicationSchedule(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    medication: fields.ForeignKeyRelation[Medication] = fields.ForeignKeyField(
        "models.Medication", related_name="schedules"
    )
    time_of_day = fields.CharEnumField(TimeOfDay, max_length=20)
    specific_time = fields.TimeField(null=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)

    class Meta:
        table = "medication_schedules"


class AdherenceLog(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    schedule: fields.ForeignKeyRelation[MedicationSchedule] = fields.ForeignKeyField(
        "models.MedicationSchedule", related_name="adherence_logs"
    )
    actor_user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="adherence_logs")
    target_date = fields.DateField()
    status = fields.CharEnumField(AdherenceStatus, max_length=20)
    logged_at = fields.DatetimeField(auto_now_add=True)
    note = fields.TextField(null=True)

    class Meta:
        table = "adherence_logs"
