"""
처방전 관련 Tortoise ORM 모델

ERD 기준:
  - prescriptions   : 처방전 헤더 (환자 정보, 병원, 상태)
  - prescription_images : 업로드된 이미지 파일 정보
"""

from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class PrescriptionStatus(StrEnum):
    """처방전 처리 상태값"""
    PENDING = "PENDING"         # 업로드만 됨, OCR 대기
    PROCESSING = "PROCESSING"   # OCR 실행 중
    COMPLETE = "COMPLETE"       # OCR 완료, 약 데이터 생성됨
    FAILED = "FAILED"           # OCR 실패


class Prescription(Model):
    """
    처방전 메인 테이블.

    - patient_id       : 실제 복약 환자 (User)
    - created_by_user_id : 처방을 업로드한 사람 (본인/보호자)
    - verification_status : OCR+약 데이터 생성 진행 상태
    """

    id = fields.BigIntField(primary_key=True)

    # FK: 환자 (User)
    patient = fields.ForeignKeyField(
        "models.User",
        related_name="prescriptions",
        on_delete=fields.CASCADE,
    )
    # FK: 업로드 주체 (User) — 보호자가 올릴 수도 있음
    created_by_user = fields.ForeignKeyField(
        "models.User",
        related_name="created_prescriptions",
        on_delete=fields.SET_NULL,
        null=True,
    )

    # 처방전 메타데이터
    hospital_name = fields.CharField(max_length=255, null=True)
    doctor_name = fields.CharField(max_length=255, null=True)
    prescription_date = fields.DateField(null=True)
    diagnosis = fields.CharField(max_length=255, null=True)

    # 상태
    verification_status = fields.CharEnumField(
        enum_type=PrescriptionStatus,
        default=PrescriptionStatus.PENDING,
        max_length=30,
    )

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "prescriptions"


class PrescriptionImage(Model):
    """
    처방전 이미지 파일 정보.
    한 처방전에 여러 장 업로드 가능 (1:N).
    """

    id = fields.BigIntField(primary_key=True)

    # FK: 처방전
    prescription = fields.ForeignKeyField(
        "models.Prescription",
        related_name="images",
        on_delete=fields.CASCADE,
    )

    # 파일 메타
    file_url = fields.CharField(max_length=512)   # 로컬 정적 경로 또는 S3 URL
    mime_type = fields.CharField(max_length=100, null=True)  # image/jpeg, image/png, application/pdf
    uploaded_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prescription_images"
