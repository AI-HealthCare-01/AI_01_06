"""
medication DTO — 기존 파일 재작성.

기준: docs/dev/api_spec.md
"""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.core.enums import TimeOfDay
from app.dtos.base import BaseSerializerModel


class MedicationDetailResponse(BaseSerializerModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    drug_name: str
    dosage: str | None = None
    frequency: str | None = None
    administration: str | None = None
    duration_days: int | None = None


class MedicationListResponse(BaseModel):
    medications: list[MedicationDetailResponse]


class ScheduleCreateRequest(BaseModel):
    medication_id: str
    time_of_day: TimeOfDay
    specific_time: str | None = None  # HH:MM
    start_date: date | None = None
    end_date: date | None = None


class ScheduleResponse(BaseSerializerModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    medication_id: str
    time_of_day: TimeOfDay
    specific_time: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class AdherenceLogRequest(BaseModel):
    schedule_id: str
    target_date: date
    note: str | None = None


class AdherenceSkipRequest(BaseModel):
    schedule_id: str
    target_date: date
    note: str | None = None


class AdherenceLogResponse(BaseSerializerModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    schedule_id: str
    target_date: date
    status: str
