"""
OCR Job Repository (B담당)
"""

from datetime import datetime

from app.core import config
from app.models.ocr_jobs import OcrJob, OcrJobStatus
from app.models.prescriptions import PrescriptionStatus


class OcrRepository:
    def __init__(self):
        self._model = OcrJob

    async def create_job(self, prescription_image_id: int, provider: str = "clova") -> OcrJob:
        return await self._model.create(
            prescription_image_id=prescription_image_id,
            provider=provider,
            status=OcrJobStatus.PENDING,
        )

    async def get_by_image_id(self, prescription_image_id: int) -> OcrJob | None:
        """이미지 1장당 최신 Job 1개 반환"""
        return (
            await self._model.filter(prescription_image_id=prescription_image_id)
            .order_by("-requested_at")
            .first()
        )

    async def get_by_id(self, job_id: int) -> OcrJob | None:
        return await self._model.get_or_none(id=job_id)

    async def get_latest_by_prescription(self, prescription_id: int) -> OcrJob | None:
        """처방전의 첫 번째 이미지에 대한 최신 OcrJob 반환"""
        return (
            await self._model.filter(
                prescription_image__prescription_id=prescription_id
            )
            .order_by("-requested_at")
            .prefetch_related("prescription_image")
            .first()
        )

    async def mark_processing(self, job_id: int) -> None:
        await self._model.filter(id=job_id).update(status=OcrJobStatus.PROCESSING)

    async def mark_complete(
        self,
        job_id: int,
        raw_ocr_json: dict,
        extracted_text: str,
        extracted_json: dict,
    ) -> None:
        await self._model.filter(id=job_id).update(
            status=OcrJobStatus.COMPLETE,
            raw_ocr_json=raw_ocr_json,
            extracted_text=extracted_text,
            extracted_json=extracted_json,
            processed_at=datetime.now(config.TIMEZONE),
        )

    async def mark_failed(self, job_id: int, error_message: str) -> None:
        await self._model.filter(id=job_id).update(
            status=OcrJobStatus.FAILED,
            error_message=error_message,
            processed_at=datetime.now(config.TIMEZONE),
        )

    async def update_extracted_json(self, job_id: int, extracted_json: dict) -> None:
        """사용자 보정 시 extracted_json만 업데이트"""
        await self._model.filter(id=job_id).update(
            extracted_json=extracted_json,
            processed_at=datetime.now(config.TIMEZONE),
        )
