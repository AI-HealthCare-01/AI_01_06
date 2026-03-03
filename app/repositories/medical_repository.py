"""
PRESCRIPTION / OCR / MEDICATION 도메인 Repository.
"""

import uuid

from app.core.enums import OcrStatus, VerificationStatus
from app.models.medicals import (
    Medication,
    OcrJob,
    Prescription,
    PrescriptionImage,
)


class PrescriptionRepository:
    async def create(
        self,
        *,
        patient_id: str,
        created_by_user_id: str,
        hospital_name: str | None = None,
        doctor_name: str | None = None,
    ) -> Prescription:
        return await Prescription.create(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            created_by_user_id=created_by_user_id,
            hospital_name=hospital_name,
            doctor_name=doctor_name,
            verification_status=VerificationStatus.DRAFT,
        )

    async def get_by_id(self, prescription_id: str) -> Prescription | None:
        return await Prescription.get_or_none(id=prescription_id)

    async def list_by_patient(self, patient_id: str) -> list[Prescription]:
        return await Prescription.filter(patient_id=patient_id).order_by("-created_at")

    async def confirm(self, prescription: Prescription) -> None:
        prescription.verification_status = VerificationStatus.CONFIRMED
        await prescription.save(update_fields=["verification_status", "updated_at"])

    async def delete(self, prescription: Prescription) -> None:
        await prescription.delete()

    async def add_image(self, prescription_id: str, file_url: str, mime_type: str | None) -> PrescriptionImage:
        return await PrescriptionImage.create(
            id=str(uuid.uuid4()),
            prescription_id=prescription_id,
            file_url=file_url,
            mime_type=mime_type,
        )


class OcrRepository:
    async def get_latest_by_image(self, prescription_image_id: str) -> OcrJob | None:
        return await OcrJob.filter(prescription_image_id=prescription_image_id).order_by("-requested_at").first()

    async def get_by_prescription(self, prescription_id: str) -> OcrJob | None:
        return (
            await OcrJob.filter(prescription_image__prescription_id=prescription_id)
            .order_by("-requested_at")
            .first()
        )

    async def update_extracted(self, ocr_job: OcrJob, extracted_json: dict) -> None:
        ocr_job.extracted_json = extracted_json
        ocr_job.status = OcrStatus.DONE
        await ocr_job.save(update_fields=["extracted_json", "status", "processed_at"])


class MedicationRepository:
    async def list_by_prescription(self, prescription_id: str) -> list[Medication]:
        return await Medication.filter(prescription_id=prescription_id, is_deleted=False)

    async def get_by_id(self, medication_id: str) -> Medication | None:
        return await Medication.get_or_none(id=medication_id, is_deleted=False)
