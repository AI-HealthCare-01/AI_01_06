from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class CaregiverRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CaregiverRequestCreate(BaseModel):
    patient_email: str
    message: str | None = None


class CaregiverRequestResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: Annotated[str, Field(alias="id")]
    status: CaregiverRequestStatus


class CaregiverRequestListResponse(BaseModel):
    requests: list[CaregiverRequestResponse]


class CaregiverApproveResponse(BaseModel):
    mapping_id: str


class PatientSummary(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: Annotated[str, Field(alias="id")]
    # 추가 환자 정보 필드 (이름, 생년월일 등)가 필요할 수 있음
    email: str | None = None


class PatientListResponse(BaseModel):
    patients: list[PatientSummary]
