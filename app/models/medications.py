"""
약(Medication) Tortoise ORM 모델

ERD 기준:
  - medications : OCR → parsed_fields 에서 생성되는 약 한 줄

A담당(auth)·B담당(OCR)·C담당(스케줄) 연결 핵심 테이블.
C담당의 medication_schedules 가 이 테이블을 참조합니다.
"""

from tortoise import fields
from tortoise.models import Model


class Medication(Model):
    """
    처방전에서 추출된 약 1종 = 1레코드.

    필드 설명:
      - drug_name      : 약품명 (예: "타이레놀정 500mg")
      - dosage         : 1회 용량 (예: "1정", "2알")
      - frequency      : 1일 횟수 (예: "3")
      - administration : 복용 방법 (예: "식후30분", "식전")
      - duration_days  : 복용 기간(일) (예: 3)
      - caution        : 주의사항 (예: "임산부 복용 주의")
      - is_deleted     : 소프트 삭제 (보정 후 재생성 시 이전 기록 보존)
    """

    id = fields.BigIntField(primary_key=True)

    # FK: 처방전
    prescription = fields.ForeignKeyField(
        "models.Prescription",
        related_name="medications",
        on_delete=fields.CASCADE,
    )

    # 약 핵심 정보 (parsed_fields 최소 스키마)
    drug_name = fields.CharField(max_length=255)
    dosage = fields.CharField(max_length=100, null=True)        # "1정", "10ml"
    frequency = fields.CharField(max_length=100, null=True)     # "3회", "아침저녁"
    administration = fields.CharField(max_length=255, null=True) # "식후30분"
    duration_days = fields.IntField(null=True)                  # 복용 기간(일)
    caution = fields.TextField(null=True)                       # 주의사항 (선택)

    # 소프트 삭제: 보정 후 재생성 시 이전 약 데이터 숨김 처리
    is_deleted = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "medications"
