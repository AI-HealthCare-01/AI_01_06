from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.redis import enqueue
from app.core.response import success_response
from app.models.guide import Guide
from app.models.prescription import Medication, Prescription
from app.models.user import User
from app.schemas.guide import GuideCreateRequest

router = APIRouter(prefix="/api/guides", tags=["guides"])


@router.post("")
async def create_guide(req: GuideCreateRequest, user: User = Depends(get_current_user)):
    prescription = await Prescription.get_or_none(id=req.prescription_id, user=user)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")

    guide = await Guide.create(
        user=user,
        prescription=prescription,
        status="generating",
    )

    await enqueue("guide_task", guide.id, user.id)

    return success_response(
        {
            "id": guide.id,
            "prescription_id": prescription.id,
            "status": guide.status,
            "created_at": str(guide.created_at),
        }
    )


@router.get("")
async def list_guides(user: User = Depends(get_current_user)):
    guides = await Guide.filter(user=user, status="completed").order_by("-created_at").prefetch_related("prescription")
    result = []
    for guide in guides:
        prescription = guide.prescription
        result.append(
            {
                "id": guide.id,
                "prescription_id": prescription.id,
                "status": guide.status,
                "prescription_info": {
                    "hospital_name": prescription.hospital_name,
                    "doctor_name": prescription.doctor_name,
                    "prescription_date": str(prescription.prescription_date)
                    if prescription.prescription_date
                    else None,
                    "diagnosis": prescription.diagnosis,
                },
                "created_at": str(guide.created_at),
            }
        )
    return success_response(result)


@router.delete("/{guide_id}")
async def delete_guide(guide_id: int, user: User = Depends(get_current_user)):
    guide = await Guide.get_or_none(id=guide_id, user=user)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    await guide.delete()
    return success_response({"message": "가이드가 삭제되었습니다."})


@router.get("/{guide_id}")
async def get_guide(guide_id: int, user: User = Depends(get_current_user)):
    guide = await Guide.get_or_none(id=guide_id, user=user)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")

    prescription = await Prescription.get(id=guide.prescription_id)
    medications = await Medication.filter(prescription=prescription)

    return success_response(
        {
            "id": guide.id,
            "prescription_id": prescription.id,
            "status": guide.status,
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
                    "duration": m.duration,
                }
                for m in medications
            ],
            "content": guide.content,
            "created_at": str(guide.created_at),
        }
    )
