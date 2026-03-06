from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.guide import Guide
from app.models.prescription import Medication, Prescription
from app.models.user import User
from app.schemas.guide import GuideCreateRequest
from app.services.guide_service import get_guide_service

router = APIRouter(prefix="/api/guides", tags=["guides"])


@router.post("")
async def create_guide(req: GuideCreateRequest, user: User = Depends(get_current_user)):
    prescription = await Prescription.get_or_none(id=req.prescription_id, user=user)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")

    medications = await Medication.filter(prescription=prescription)
    med_list = [
        {
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "duration": m.duration,
            "instructions": m.instructions,
        }
        for m in medications
    ]

    user_info = {
        "name": user.name,
        "height": user.height,
        "weight": user.weight,
        "allergies": user.allergies,
        "conditions": user.conditions,
    }

    guide_service = get_guide_service()
    content = await guide_service.generate(med_list, user_info)

    guide = await Guide.create(
        user=user,
        prescription=prescription,
        content=content,
    )

    return success_response({
        "id": guide.id,
        "prescription_id": prescription.id,
        "content": guide.content,
        "created_at": str(guide.created_at),
    })


@router.get("/{guide_id}")
async def get_guide(guide_id: int, user: User = Depends(get_current_user)):
    guide = await Guide.get_or_none(id=guide_id, user=user)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")

    prescription = await Prescription.get(id=guide.prescription_id)
    medications = await Medication.filter(prescription=prescription)

    return success_response({
        "id": guide.id,
        "prescription_id": prescription.id,
        "prescription_info": {
            "hospital_name": prescription.hospital_name,
            "doctor_name": prescription.doctor_name,
            "prescription_date": str(prescription.prescription_date) if prescription.prescription_date else None,
            "diagnosis": prescription.diagnosis,
        },
        "medications": [
            {
                "id": m.id,
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
            }
            for m in medications
        ],
        "content": guide.content,
        "created_at": str(guide.created_at),
    })
