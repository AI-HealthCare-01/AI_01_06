"""
처방전 Repository (B담당)

DB 쿼리만 담당합니다. 비즈니스 로직은 포함하지 않습니다.
"""

from datetime import datetime

from app.core import config
from app.models.prescriptions import Prescription, PrescriptionImage, PrescriptionStatus


class PrescriptionRepository:
    def __init__(self):
        self._model = Prescription
        self._image_model = PrescriptionImage

    # ─── Prescription CRUD ────────────────────────────────────────────────────

    async def create(
        self,
        patient_id: int,
        created_by_user_id: int,
        hospital_name: str | None = None,
        doctor_name: str | None = None,
        prescription_date=None,
        diagnosis: str | None = None,
    ) -> Prescription:
        return await self._model.create(
            patient_id=patient_id,
            created_by_user_id=created_by_user_id,
            hospital_name=hospital_name,
            doctor_name=doctor_name,
            prescription_date=prescription_date,
            diagnosis=diagnosis,
            verification_status=PrescriptionStatus.PENDING,
        )

    async def get_by_id(self, prescription_id: int) -> Prescription | None:
        return await self._model.get_or_none(id=prescription_id)

    async def get_by_id_with_images(self, prescription_id: int) -> Prescription | None:
        """처방전 + 이미지들을 prefetch해서 반환"""
        return await self._model.get_or_none(id=prescription_id).prefetch_related("images")

    async def get_list_by_patient(self, patient_id: int) -> list[Prescription]:
        return await self._model.filter(patient_id=patient_id).order_by("-created_at").all()

    async def update_status(self, prescription_id: int, status: PrescriptionStatus) -> None:
        await self._model.filter(id=prescription_id).update(
            verification_status=status,
            updated_at=datetime.now(config.TIMEZONE),
        )

    # ─── PrescriptionImage CRUD ───────────────────────────────────────────────

    async def create_image(
        self,
        prescription_id: int,
        file_url: str,
        mime_type: str | None = None,
    ) -> PrescriptionImage:
        return await self._image_model.create(
            prescription_id=prescription_id,
            file_url=file_url,
            mime_type=mime_type,
        )

    async def get_images_by_prescription(self, prescription_id: int) -> list[PrescriptionImage]:
        return await self._image_model.filter(prescription_id=prescription_id).all()
