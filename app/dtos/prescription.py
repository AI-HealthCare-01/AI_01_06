from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class PrescriptionUploadResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    prescription_id: Annotated[str, Field(alias="id")]
    status: Annotated[str, Field(description="PROCESSING, COMPLETE, FAILED")]
    uploaded_at: Annotated[datetime, Field(alias="created_at")]


class PrescriptionDetailResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    prescription_id: Annotated[str, Field(alias="id")]
    hospital_name: str | None = None
    doctor_name: str | None = None
    diagnosis: str | None = None
    prescribed_date: Annotated[date | None, Field(alias="prescription_date")]
    status: Annotated[str | None, Field(alias="verification_status")]


class PrescriptionListResponse(BaseModel):
    prescriptions: list[PrescriptionDetailResponse]
    total: int
    page: int


class OcrResultResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    ocr_id: Annotated[str, Field(alias="id")]
    raw_text: Annotated[str | None, Field(alias="extracted_text")]
    parsed_fields: Annotated[dict | None, Field(alias="extracted_json")]


class OcrUpdateRequest(BaseModel):
    parsed_fields: dict
