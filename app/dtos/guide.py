"""
guide DTO — 기존 파일 재작성.

기준: docs/dev/api_spec.md
"""

from datetime import datetime

from pydantic import ConfigDict

from app.dtos.base import BaseSerializerModel


class GuideResponse(BaseSerializerModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prescription_id: str
    guide_markdown: str
    precautions: str | None = None
    lifestyle_advice: str | None = None
    summary_json: dict | None = None
    generated_at: datetime
