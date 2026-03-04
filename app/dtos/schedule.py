from datetime import date, datetime, time
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class AlarmChannel(str, Enum):
    WEB = "WEB"
    PUSH = "PUSH"
    SMS = "SMS"


class ScheduleCreateRequest(BaseModel):
    medication_id: str
    times: list[str] = Field(..., description="복용 시간 배열 (예: ['08:00', '20:00'])")
    start_date: date
    end_date: date
    alarm_enabled: bool
    alarm_channel: AlarmChannel | None = None


class ScheduleCreateResponse(BaseModel):
    schedule_id: str
    instance_count: int


class ScheduleSummaryResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    schedule_id: Annotated[str, Field(alias="id")]
    start_date: date | None = None
    end_date: date | None = None


class ScheduleListResponse(BaseModel):
    schedules: list[ScheduleSummaryResponse]


class ScheduleUpdateRequest(BaseModel):
    times: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    alarm_enabled: bool | None = None


class InstanceStatus(str, Enum):
    PENDING = "PENDING"
    TAKEN = "TAKEN"
    SKIPPED = "SKIPPED"


class ScheduleInstanceResponse(BaseSerializerModel):
    # 이행 인스턴스 정보 (현재 AdherenceLog와 연동됨)
    status: InstanceStatus
    scheduled_date: date
    scheduled_time: time | None = None


class AdherenceCreateRequest(BaseModel):
    instance_id: str
    taken_at: datetime | None = None


class AdherenceSkipRequest(BaseModel):
    instance_id: str
    reason: str | None = None


class AdherenceRecordResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    adherence_id: Annotated[str, Field(alias="id")]
    status: str


class AdherenceStatResponse(BaseModel):
    adherence_rate: float
    total_scheduled: int
    total_taken: int
