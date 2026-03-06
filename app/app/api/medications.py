from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.prescription import Medication
from app.models.user import User

router = APIRouter(prefix="/api/medications", tags=["medications"])


@router.get("/{medication_id}")
async def get_medication(medication_id: int, user: User = Depends(get_current_user)):
    medication = await Medication.get_or_none(id=medication_id)
    if not medication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="약물 정보를 찾을 수 없습니다.")
    return success_response(
        {
            "id": medication.id,
            "name": medication.name,
            "dosage": medication.dosage,
            "frequency": medication.frequency,
            "duration": medication.duration,
            "instructions": medication.instructions,
        }
    )
