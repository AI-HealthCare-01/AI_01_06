"""
CAREGIVER 도메인 DTO.
"""

from pydantic import BaseModel

from app.core.enums import CaregiverMappingStatus
from app.dtos.base import BaseSerializerModel


class CaregiverRequestBody(BaseModel):
    patient_id: str


class CaregiverMappingResponse(BaseSerializerModel):
    caregiver_id: str
    patient_id: str
    status: CaregiverMappingStatus
