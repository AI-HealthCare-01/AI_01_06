import logging
import os

from app.models.prescription import Medication, Prescription
from app.services.icd_service import normalize_dosage, resolve_diagnosis, validate_doctor_name
from app.services.ocr_service import get_ocr_service

logger = logging.getLogger(__name__)


async def ocr_task(ctx: dict, prescription_id: int, filepath: str) -> None:
    """Run OCR on a prescription image and save results."""
    prescription = await Prescription.get(id=prescription_id)

    ocr_service = get_ocr_service()
    try:
        ocr_result = await ocr_service.extract(filepath)

        prescription.hospital_name = ocr_result.get("hospital_name")
        prescription.doctor_name = validate_doctor_name(ocr_result.get("doctor_name"))
        prescription.prescription_date = ocr_result.get("prescription_date")
        prescription.diagnosis = await resolve_diagnosis(ocr_result.get("diagnosis"))
        prescription.ocr_raw = ocr_result
        prescription.ocr_status = "ocr_completed"
        await prescription.save()

        for med_data in ocr_result.get("medications", []):
            await Medication.create(
                prescription=prescription,
                name=med_data["name"],
                dosage=normalize_dosage(med_data.get("dosage")),
                frequency=med_data.get("frequency"),
                duration=med_data.get("duration"),
                instructions=med_data.get("instructions"),
            )
    except Exception:
        logger.exception("OCR failed for prescription %d", prescription_id)
        prescription.ocr_status = "ocr_failed"
        await prescription.save()
    finally:
        try:
            os.remove(filepath)
        except OSError:
            pass
