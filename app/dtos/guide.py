from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class GuideStyle(str, Enum):
    SIMPLE = "SIMPLE"
    DETAILED = "DETAILED"


class GuideCreateRequest(BaseModel):
    prescription_id: str
    style: GuideStyle | None = GuideStyle.SIMPLE


class GuideCreateResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    guide_id: Annotated[str, Field(alias="id")]
    content: str


class GuideDetailResponse(BaseSerializerModel):
    content: str


class GuidePdfResponse(BaseModel):
    file_url: str
