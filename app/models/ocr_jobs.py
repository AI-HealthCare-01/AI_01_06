"""
OCR 작업(Job) Tortoise ORM 모델

ERD 기준:
  - ocr_jobs : CLOVA OCR 실행 단위 (이미지 1장 → Job 1개)
"""

from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class OcrJobStatus(StrEnum):
    """OCR 작업 진행 상태"""
    PENDING = "PENDING"         # 생성됨, 아직 호출 전
    PROCESSING = "PROCESSING"   # OCR API 호출 중
    COMPLETE = "COMPLETE"       # 성공, extracted_json 저장됨
    FAILED = "FAILED"           # 실패 (재시도 가능)


class OcrJob(Model):
    """
    CLOVA OCR API 호출 1회 = OcrJob 1건.

    - raw_ocr_json    : CLOVA API 원본 응답 (JSON 문자열)
    - extracted_text  : OCR로 뽑아낸 전체 텍스트
    - extracted_json  : GPT가 구조화한 parsed_fields JSON
                        {
                          "medications": [
                            {
                              "drug_name": "타이레놀정",
                              "dosage": "1정",
                              "frequency": "3",
                              "administration": "식후30분",
                              "duration_days": 3,
                              "caution": "임산부 주의"
                            }, ...
                          ]
                        }
    """

    id = fields.BigIntField(primary_key=True)

    # FK: 이미지 1장 ↔ Job 1개
    prescription_image = fields.ForeignKeyField(
        "models.PrescriptionImage",
        related_name="ocr_jobs",
        on_delete=fields.CASCADE,
    )

    provider = fields.CharField(max_length=50, default="clova")   # 확장성: clova / mock / ...

    status = fields.CharEnumField(
        enum_type=OcrJobStatus,
        default=OcrJobStatus.PENDING,
        max_length=30,
    )

    # CLOVA 원본 응답 전체 (디버깅·재파싱용)
    raw_ocr_json = fields.JSONField(null=True)

    # OCR로 추출된 전체 텍스트
    extracted_text = fields.TextField(null=True)

    # GPT로 구조화된 약 데이터 (parsed_fields)
    extracted_json = fields.JSONField(null=True)

    # 타임스탬프
    requested_at = fields.DatetimeField(auto_now_add=True)
    processed_at = fields.DatetimeField(null=True)

    # 실패 시 이유
    error_message = fields.TextField(null=True)

    class Meta:
        table = "ocr_jobs"
