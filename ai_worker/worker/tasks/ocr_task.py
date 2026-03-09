from app.models.guide import Guide
from app.models.prescription import Medication, Prescription
from app.services.ocr_service import get_ocr_service


async def ocr_task(ctx: dict, prescription_id: int) -> None:
    """Run OCR on a prescription image and save results."""
    prescription = await Prescription.get(id=prescription_id)

    ocr_service = get_ocr_service()
    ocr_result = await ocr_service.extract(prescription.image_path)

    prescription.hospital_name = ocr_result.get("hospital_name")
    prescription.doctor_name = ocr_result.get("doctor_name")
    prescription.prescription_date = ocr_result.get("prescription_date")
    prescription.diagnosis = ocr_result.get("diagnosis")
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

    user = await prescription.user
    guide = await Guide.create(user=user, prescription=prescription, status="generating")
    await ctx["redis"].enqueue_job("guide_task", guide.id, user.id)
