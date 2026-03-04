"""
처방전·OCR·약 관련 Pydantic DTO (요청/응답 스키마)

B담당 API 엔드포인트에서 사용합니다.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ─── 공통 직렬화 기반 ────────────────────────────────────────────────────────

class BaseOrmModel(BaseModel):
    """Tortoise ORM 객체를 직접 직렬화할 때 사용하는 기반 클래스"""
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 처방전 (Prescription)
# ═══════════════════════════════════════════════════════════════════════════════

class PrescriptionCreateRequest(BaseModel):
    """
    처방전 업로드 요청 시 함께 보내는 메타데이터.
    - 이미지 파일은 multipart/form-data의 File 파트로 따로 전송됩니다.
    """
    patient_id: int = Field(..., description="복약 환자 user_id (본인이면 자신의 id)")
    hospital_name: str | None = Field(None, max_length=255, description="병원명")
    doctor_name: str | None = Field(None, max_length=255, description="의사명")
    prescription_date: date | None = Field(None, description="처방일 (YYYY-MM-DD)")
    diagnosis: str | None = Field(None, max_length=255, description="진단명")


class PrescriptionResponse(BaseOrmModel):
    """처방전 요약 응답"""
    id: int
    patient_id: int
    created_by_user_id: int | None
    hospital_name: str | None
    doctor_name: str | None
    prescription_date: date | None
    diagnosis: str | None
    verification_status: str
    created_at: datetime
    updated_at: datetime


class PrescriptionDetailResponse(PrescriptionResponse):
    """처방전 상세 응답 (이미지 URL + 약 목록 포함)"""
    image_urls: list[str] = []
    medications: list[MedicationResponse] = []
    ocr_status: str | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# OCR 결과 (OcrJob)
# ═══════════════════════════════════════════════════════════════════════════════

class OcrResultResponse(BaseOrmModel):
    """OCR 작업 결과 조회 응답"""
    id: int
    prescription_image_id: int
    provider: str
    status: str
    extracted_text: str | None
    extracted_json: dict[str, Any] | None   # parsed_fields (약 구조화 데이터)
    requested_at: datetime
    processed_at: datetime | None
    error_message: str | None


class OcrCorrectionRequest(BaseModel):
    """
    OCR 결과 사용자 보정 요청.

    - extracted_json: 수정된 parsed_fields 전체를 덮어씁니다.
    - regenerate: True이면 기존 medications를 소프트삭제하고 재생성합니다.
    """
    extracted_json: dict[str, Any] = Field(
        ...,
        description="수정된 parsed_fields 전체 ({medications: [...]})",
        example={
            "medications": [
                {
                    "drug_name": "타이레놀정500mg",
                    "dosage": "1정",
                    "frequency": "3",
                    "administration": "식후30분",
                    "duration_days": 3,
                    "caution": "",
                }
            ]
        },
    )
    regenerate: bool = Field(
        True,
        description="True이면 기존 medications 소프트삭제 후 재생성",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 약 (Medication)
# ═══════════════════════════════════════════════════════════════════════════════

class MedicationResponse(BaseOrmModel):
    """약 1건 응답"""
    id: int
    prescription_id: int
    drug_name: str
    dosage: str | None
    frequency: str | None
    administration: str | None
    duration_days: int | None
    caution: str | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class MedicationUpdateRequest(BaseModel):
    """약 수동 수정 요청 (PATCH 방식 — 보낸 필드만 업데이트)"""
    drug_name: str | None = Field(None, max_length=255)
    dosage: str | None = Field(None, max_length=100)
    frequency: str | None = Field(None, max_length=100)
    administration: str | None = Field(None, max_length=255)
    duration_days: int | None = None
    caution: str | None = None


# ─── 순환 참조 해소 (Python 3.10+ 방식) ──────────────────────────────────────
PrescriptionDetailResponse.model_rebuild()
