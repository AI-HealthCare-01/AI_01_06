import logging
import os

from arq.connections import RedisSettings
from tortoise import Tortoise

from app import config
from app.core.database import TORTOISE_ORM
from app.models.prescription import Medication, Prescription
from app.services.icd_service import resolve_diagnosis
from app.services.ocr_service import get_ocr_service

logger = logging.getLogger(__name__)


async def ocr_task(ctx, prescription_id: int, filepath: str) -> None:
    prescription = await Prescription.get_or_none(id=prescription_id)
    if not prescription:
        logger.error("Prescription %d not found", prescription_id)
        _delete_file(filepath)
        return

    try:
        ocr_service = get_ocr_service()
        ocr_result = await ocr_service.extract(filepath)

        prescription.hospital_name = ocr_result.get("hospital_name")
        prescription.doctor_name = ocr_result.get("doctor_name")
        prescription.prescription_date = ocr_result.get("prescription_date")
        prescription.diagnosis = await resolve_diagnosis(ocr_result.get("diagnosis"))
        prescription.ocr_raw = ocr_result
        prescription.ocr_status = "ocr_completed"
        await prescription.save()

        for med_data in ocr_result.get("medications", []):
            await Medication.create(
                prescription=prescription,
                name=med_data["name"],
                dosage=med_data.get("dosage"),
                frequency=med_data.get("frequency"),
                duration=med_data.get("duration"),
                instructions=med_data.get("instructions"),
            )

    except Exception:
        logger.exception("OCR failed for prescription %d", prescription_id)
        prescription.ocr_status = "ocr_failed"
        await prescription.save()

    finally:
        _delete_file(filepath)


def _delete_file(filepath: str) -> None:
    try:
        os.remove(filepath)
    except OSError:
        pass


async def startup(ctx) -> None:
    await Tortoise.init(config=TORTOISE_ORM)


async def shutdown(ctx) -> None:
    await Tortoise.close_connections()


class WorkerSettings:
    functions = [ocr_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
