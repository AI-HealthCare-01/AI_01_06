from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class MedicationSummary(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    medication_id: Annotated[str, Field(alias="id")]
    name: Annotated[str, Field(alias="drug_name")]
    ingredient: str | None = None  # TODO: 성분 필드는 모델에 없음, 향후 확장 필요
    dosage: str | None = None
    frequency_per_day: Annotated[str | None, Field(alias="frequency")]
    duration_days: int | None = None


class MedicationListResponse(BaseModel):
    medications: list[MedicationSummary]


class MedicationDetailResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    medication_id: Annotated[str, Field(alias="id")]
    name: Annotated[str, Field(alias="drug_name")]
    warnings: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
