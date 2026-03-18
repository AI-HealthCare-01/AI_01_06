import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.deps import get_acting_patient
from app.core.redis import enqueue
from app.core.response import success_response
from app.models.prescription import Medication, Prescription
from app.models.user import User
from app.schemas.prescription import OcrUpdateRequest
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")


@router.post("")
async def upload_prescription(file: UploadFile, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "image.png")[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    prescription = await Prescription.create(
        user=target_user,
        acted_by=current_user if patient else None,
        ocr_status="processing",
    )

    await enqueue("ocr_task", prescription.id, filepath)

    return success_response(
        {
            "id": prescription.id,
            "ocr_status": prescription.ocr_status,
        }
    )


@router.get("")
async def list_prescriptions(actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    prescriptions = await Prescription.filter(user=target_user).order_by("-created_at")
    result = []
    for p in prescriptions:
        med_count = await Medication.filter(prescription=p).count()
        result.append(
            {
                "id": p.id,
                "hospital_name": p.hospital_name,
                "doctor_name": p.doctor_name,
                "prescription_date": str(p.prescription_date) if p.prescription_date else None,
                "diagnosis": p.diagnosis,
                "ocr_status": p.ocr_status,
                "medication_count": med_count,
                "created_at": str(p.created_at),
            }
        )
    return success_response(result)


@router.get("/{prescription_id}")
async def get_prescription(prescription_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    prescription = await Prescription.get_or_none(id=prescription_id, user=target_user)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")
    return success_response(
        {
            "id": prescription.id,
            "hospital_name": prescription.hospital_name,
            "doctor_name": prescription.doctor_name,
            "prescription_date": str(prescription.prescription_date) if prescription.prescription_date else None,
            "diagnosis": prescription.diagnosis,
            "ocr_status": prescription.ocr_status,
            "created_at": str(prescription.created_at),
        }
    )


@router.delete("/{prescription_id}")
async def delete_prescription(prescription_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    prescription = await Prescription.get_or_none(id=prescription_id, user=target_user)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")
    await Medication.filter(prescription=prescription).delete()
    await prescription.delete()
    return success_response({"message": "처방전이 삭제되었습니다."})


@router.get("/{prescription_id}/ocr")
async def get_ocr_result(prescription_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    prescription = await Prescription.get_or_none(id=prescription_id, user=target_user)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")
    medications = await Medication.filter(prescription=prescription)
    med_list = [
        {
            "id": m.id,
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "duration": m.duration,
            "instructions": m.instructions,
        }
        for m in medications
    ]
    return success_response(
        {
            "hospital_name": prescription.hospital_name,
            "doctor_name": prescription.doctor_name,
            "prescription_date": str(prescription.prescription_date) if prescription.prescription_date else None,
            "diagnosis": prescription.diagnosis,
            "medications": med_list,
        }
    )


@router.put("/{prescription_id}/ocr")
async def update_ocr_result(
    prescription_id: int,
    req: OcrUpdateRequest,
    actors: tuple[User, User | None] = Depends(get_acting_patient),
):
    current_user, patient = actors
    target_user = patient or current_user
    prescription = await Prescription.get_or_none(id=prescription_id, user=target_user)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")

    prescription.hospital_name = req.hospital_name
    prescription.doctor_name = req.doctor_name
    prescription.prescription_date = req.prescription_date
    prescription.diagnosis = req.diagnosis
    prescription.ocr_status = "confirmed"
    await prescription.save()

    await Medication.filter(prescription=prescription).delete()
    for med in req.medications:
        await Medication.create(
            prescription=prescription,
            name=med.name,
            dosage=med.dosage,
            frequency=med.frequency,
            duration=med.duration,
            instructions=med.instructions,
        )

    return success_response({"message": "처방전 내용이 수정되었습니다."})


@router.get("/{prescription_id}/medications")
async def list_medications(prescription_id: int, actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user
    prescription = await Prescription.get_or_none(id=prescription_id, user=target_user)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")
    medications = await Medication.filter(prescription=prescription)
    result = [
        {
            "id": m.id,
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "duration": m.duration,
            "instructions": m.instructions,
        }
        for m in medications
    ]
    return success_response(result)
