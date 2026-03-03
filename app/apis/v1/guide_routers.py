"""
GUIDE / SCHEDULE / ADHERENCE 도메인 라우터.

기준: docs/dev/api_spec.md
  POST /api/guides
  GET  /api/guides/{guide_id}
  GET  /api/guides/{guide_id}/pdf
  POST /api/schedules
  GET  /api/schedules
  GET  /api/schedule-instances
  GET  /api/schedule-instances/{instance_id}
  PATCH  /api/schedules/{schedule_id}
  DELETE /api/schedules/{schedule_id}
  POST /api/adherence
  POST /api/adherence/skip
  GET  /api/adherence
  GET  /api/adherence/stat
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response

from app.core.enums import AdherenceStatus
from app.dependencies.security import get_request_user
from app.dtos.guide import GuideResponse
from app.dtos.medication import (
    AdherenceLogRequest,
    AdherenceLogResponse,
    AdherenceSkipRequest,
    ScheduleCreateRequest,
    ScheduleResponse,
)
from app.models.users import User
from app.repositories.guide_repository import AdherenceRepository, GuideRepository, ScheduleRepository

guide_router = APIRouter(prefix="/guides", tags=["guides"])
schedule_router = APIRouter(prefix="/schedules", tags=["schedules"])
schedule_instance_router = APIRouter(prefix="/schedule-instances", tags=["schedules"])
adherence_router = APIRouter(prefix="/adherence", tags=["adherence"])

_guide_repo = GuideRepository()
_schedule_repo = ScheduleRepository()
_adherence_repo = AdherenceRepository()


# ── GUIDE ──────────────────────────────────

@guide_router.post("", status_code=status.HTTP_201_CREATED)
async def create_guide(
    prescription_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-GUIDE-001: 확정된 처방전 기반 LLM 복약 가이드 생성 (ai_worker 연동 예정)."""
    existing = await _guide_repo.get_by_prescription(prescription_id)
    if existing:
        return Response(
            content={"guide_id": existing.id, "detail": "이미 생성된 가이드가 있습니다."},
            status_code=status.HTTP_200_OK,
        )
    guide = await _guide_repo.create(
        prescription_id=prescription_id,
        guide_markdown="# 복약 가이드\n> AI 가이드 생성 중입니다.",
    )
    return Response(content={"guide_id": guide.id}, status_code=status.HTTP_201_CREATED)


@guide_router.get("/{guide_id}", status_code=status.HTTP_200_OK)
async def get_guide(
    guide_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-GUIDE-003: 약물별 상세 복약법 및 주의사항 조회."""
    guide = await _guide_repo.get_by_id(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    return Response(
        content=GuideResponse.model_validate(guide).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


@guide_router.get("/{guide_id}/pdf", status_code=status.HTTP_200_OK)
async def download_guide_pdf(
    guide_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """가이드 PDF 다운로드 (추후 구현)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="PDF 다운로드는 추후 지원됩니다.")


# ── SCHEDULE ──────────────────────────────────

@schedule_router.post("", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    body: ScheduleCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    schedule = await _schedule_repo.create(
        medication_id=body.medication_id,
        time_of_day=body.time_of_day,
        specific_time=body.specific_time,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return Response(
        content=ScheduleResponse.model_validate(schedule).model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )


@schedule_router.get("", status_code=status.HTTP_200_OK)
async def list_schedules(
    medication_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    schedules = await _schedule_repo.list_by_medication(medication_id)
    data = [ScheduleResponse.model_validate(s).model_dump(mode="json") for s in schedules]
    return Response(content={"schedules": data}, status_code=status.HTTP_200_OK)


@schedule_router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    schedule = await _schedule_repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="스케줄을 찾을 수 없습니다.")
    await _schedule_repo.delete(schedule)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


# ── ADHERENCE ──────────────────────────────────

@adherence_router.post("", status_code=status.HTTP_201_CREATED)
async def log_adherence(
    body: AdherenceLogRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """복약 완료 체크."""
    log = await _adherence_repo.log(
        schedule_id=body.schedule_id,
        actor_user_id=user.id,
        target_date=body.target_date,
        status=AdherenceStatus.TAKEN,
        note=body.note,
    )
    return Response(
        content=AdherenceLogResponse.model_validate(log).model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )


@adherence_router.post("/skip", status_code=status.HTTP_201_CREATED)
async def skip_adherence(
    body: AdherenceSkipRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """복약 스킵 체크."""
    log = await _adherence_repo.log(
        schedule_id=body.schedule_id,
        actor_user_id=user.id,
        target_date=body.target_date,
        status=AdherenceStatus.SKIPPED,
        note=body.note,
    )
    return Response(
        content=AdherenceLogResponse.model_validate(log).model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )


@adherence_router.get("", status_code=status.HTTP_200_OK)
async def list_adherence(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    logs = await _adherence_repo.list_by_patient(user.id)
    data = [AdherenceLogResponse.model_validate(log).model_dump(mode="json") for log in logs]
    return Response(content={"logs": data}, status_code=status.HTTP_200_OK)


@adherence_router.get("/stat", status_code=status.HTTP_200_OK)
async def adherence_stat(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    logs = await _adherence_repo.list_by_patient(user.id)
    taken = sum(1 for log in logs if log.status == AdherenceStatus.TAKEN)
    skipped = sum(1 for log in logs if log.status == AdherenceStatus.SKIPPED)
    total = len(logs)
    rate = round(taken / total * 100, 1) if total else 0.0
    return Response(
        content={"total": total, "taken": taken, "skipped": skipped, "adherence_rate": rate},
        status_code=status.HTTP_200_OK,
    )
