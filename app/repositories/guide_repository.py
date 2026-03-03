"""
GUIDE / SCHEDULE / ADHERENCE 도메인 Repository.
"""

import uuid
from datetime import date

from app.core.enums import AdherenceStatus
from app.models.guides import MedicationGuide
from app.models.medicals import AdherenceLog, MedicationSchedule


class GuideRepository:
    async def get_by_id(self, guide_id: str) -> MedicationGuide | None:
        return await MedicationGuide.get_or_none(id=guide_id)

    async def get_by_prescription(self, prescription_id: str) -> MedicationGuide | None:
        return await MedicationGuide.get_or_none(prescription_id=prescription_id)

    async def create(
        self,
        *,
        prescription_id: str,
        guide_markdown: str,
        precautions: str | None = None,
        lifestyle_advice: str | None = None,
        summary_json: dict | None = None,
    ) -> MedicationGuide:
        return await MedicationGuide.create(
            id=str(uuid.uuid4()),
            prescription_id=prescription_id,
            guide_markdown=guide_markdown,
            precautions=precautions,
            lifestyle_advice=lifestyle_advice,
            summary_json=summary_json,
        )


class ScheduleRepository:
    async def list_by_medication(self, medication_id: str) -> list[MedicationSchedule]:
        return await MedicationSchedule.filter(medication_id=medication_id)

    async def get_by_id(self, schedule_id: str) -> MedicationSchedule | None:
        return await MedicationSchedule.get_or_none(id=schedule_id)

    async def create(self, *, medication_id: str, time_of_day: str, specific_time=None, start_date=None, end_date=None) -> MedicationSchedule:
        return await MedicationSchedule.create(
            id=str(uuid.uuid4()),
            medication_id=medication_id,
            time_of_day=time_of_day,
            specific_time=specific_time,
            start_date=start_date,
            end_date=end_date,
        )

    async def delete(self, schedule: MedicationSchedule) -> None:
        await schedule.delete()


class AdherenceRepository:
    async def list_by_patient(self, actor_user_id: str) -> list[AdherenceLog]:
        return await AdherenceLog.filter(actor_user_id=actor_user_id).order_by("-target_date")

    async def log(
        self,
        *,
        schedule_id: str,
        actor_user_id: str,
        target_date: date,
        status: AdherenceStatus,
        note: str | None = None,
    ) -> AdherenceLog:
        return await AdherenceLog.create(
            id=str(uuid.uuid4()),
            schedule_id=schedule_id,
            actor_user_id=actor_user_id,
            target_date=target_date,
            status=status,
            note=note,
        )
