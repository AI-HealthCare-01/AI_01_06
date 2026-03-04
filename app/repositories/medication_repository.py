"""
Medication Repository (B담당)
"""

from datetime import datetime
from typing import Any

from app.core import config
from app.models.medications import Medication


class MedicationRepository:
    def __init__(self):
        self._model = Medication

    async def bulk_create(
        self, prescription_id: int, medications_data: list[dict[str, Any]]
    ) -> list[Medication]:
        """
        OCR parsed_fields의 medications 리스트 → Medication 레코드 일괄 생성.

        medications_data 예시:
          [
            {
              "drug_name": "타이레놀정",
              "dosage": "1정",
              "frequency": "3",
              "administration": "식후30분",
              "duration_days": 3,
              "caution": ""
            }
          ]
        """
        objs = [
            Medication(
                prescription_id=prescription_id,
                drug_name=item.get("drug_name", "알 수 없음"),
                dosage=item.get("dosage"),
                frequency=item.get("frequency"),
                administration=item.get("administration"),
                duration_days=item.get("duration_days"),
                caution=item.get("caution") or None,
                is_deleted=False,
            )
            for item in medications_data
            if item.get("drug_name")  # drug_name이 있는 항목만
        ]
        await Medication.bulk_create(objs)
        # bulk_create는 id를 채우지 않으므로 DB에서 다시 조회
        return await self._model.filter(
            prescription_id=prescription_id, is_deleted=False
        ).all()

    async def get_active_by_prescription(self, prescription_id: int) -> list[Medication]:
        """소프트 삭제되지 않은 약 목록"""
        return await self._model.filter(
            prescription_id=prescription_id, is_deleted=False
        ).order_by("id").all()

    async def get_by_id(self, medication_id: int) -> Medication | None:
        return await self._model.get_or_none(id=medication_id, is_deleted=False)

    async def update(self, medication: Medication, data: dict[str, Any]) -> Medication:
        for key, value in data.items():
            if value is not None:
                setattr(medication, key, value)
        medication.updated_at = datetime.now(config.TIMEZONE)
        await medication.save()
        return medication

    async def soft_delete_all_by_prescription(self, prescription_id: int) -> None:
        """보정 후 재생성 시 기존 약 소프트 삭제"""
        await self._model.filter(prescription_id=prescription_id, is_deleted=False).update(
            is_deleted=True,
            updated_at=datetime.now(config.TIMEZONE),
        )
