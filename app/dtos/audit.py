from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class AuditLogItem(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    action_type: str
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str
    outcome: str | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogItem]
