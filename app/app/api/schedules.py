from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import get_acting_patient, get_current_user
from app.core.response import success_response
from app.models.prescription import Medication
from app.models.schedule import AdherenceLog, MedicationSchedule
from app.models.user import User

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class ScheduleCreateItem(BaseModel):
    medication_id: int
    time_of_day: str  # MORNING|NOON|EVENING|BEDTIME
    start_date: str | None = None
    end_date: str | None = None


class AdherenceLogRequest(BaseModel):
    target_date: str
    status: str  # TAKEN|MISSED|SKIPPED
    note: str | None = None


@router.post("")
async def create_schedules(items: list[ScheduleCreateItem], user: User = Depends(get_current_user)):
    valid_times = {"MORNING", "NOON", "EVENING", "BEDTIME"}
    results = []
    for item in items:
        if item.time_of_day not in valid_times:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"time_of_day는 {valid_times} 중 하나여야 합니다.",
            )
        med = await Medication.get_or_none(id=item.medication_id)
        if not med:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"약물 {item.medication_id}를 찾을 수 없습니다."
            )
        await med.fetch_related("prescription")
        if med.prescription.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")

        schedule = await MedicationSchedule.create(
            medication=med,
            time_of_day=item.time_of_day,
            start_date=date.fromisoformat(item.start_date) if item.start_date else None,
            end_date=date.fromisoformat(item.end_date) if item.end_date else None,
        )
        results.append({"id": schedule.id, "time_of_day": schedule.time_of_day})
    return success_response(results)


@router.get("/today")
async def get_today_schedules(actors: tuple = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    today = date.today()
    schedules = await MedicationSchedule.filter(
        start_date__lte=today,
        end_date__gte=today,
        medication__prescription__user=target_user,
    ).prefetch_related("medication")

    schedule_ids = [s.id for s in schedules]
    today_logs = await AdherenceLog.filter(schedule_id__in=schedule_ids, target_date=today)
    log_by_schedule: dict[int, AdherenceLog] = {log.schedule_id: log for log in today_logs}

    result = []
    for s in schedules:
        today_log = log_by_schedule.get(s.id)
        result.append(
            {
                "id": s.id,
                "medication_id": s.medication.id,
                "medication_name": s.medication.name,
                "dosage": s.medication.dosage,
                "frequency": s.medication.frequency,
                "time_of_day": s.time_of_day,
                "today_status": today_log.status if today_log else None,
                "today_log_id": today_log.id if today_log else None,
            }
        )
    return success_response(result)


@router.post("/{schedule_id}/log")
async def log_adherence(schedule_id: int, req: AdherenceLogRequest, actors: tuple = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user

    valid_statuses = {"TAKEN", "MISSED", "SKIPPED"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"status는 {valid_statuses} 중 하나여야 합니다.",
        )

    schedule = await MedicationSchedule.get_or_none(id=schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="스케줄을 찾을 수 없습니다.")
    await schedule.fetch_related("medication__prescription")
    if schedule.medication.prescription.user_id != target_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")

    log = await AdherenceLog.create(
        schedule=schedule,
        actor_user=current_user,
        target_date=date.fromisoformat(req.target_date),
        status=req.status,
        note=req.note,
    )
    return success_response({"id": log.id, "status": log.status})


@router.get("/{schedule_id}/logs")
async def get_logs(schedule_id: int, user: User = Depends(get_current_user)):
    schedule = await MedicationSchedule.get_or_none(id=schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="스케줄을 찾을 수 없습니다.")

    await schedule.fetch_related("medication__prescription")
    if schedule.medication.prescription.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")

    logs = await AdherenceLog.filter(schedule=schedule).order_by("-target_date")
    result = [{"id": lg.id, "target_date": str(lg.target_date), "status": lg.status, "note": lg.note} for lg in logs]
    return success_response(result)
