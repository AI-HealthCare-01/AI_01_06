from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.patient_profile import PatientProfile
from app.models.user import User
from app.schemas.user import UserUpdateRequest

router = APIRouter(prefix="/api/users", tags=["users"])

_PATIENT_PROFILE_FIELDS = {"height_cm", "weight_kg", "allergy_details", "disease_details"}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    profile = None
    if user.role == "PATIENT":
        profile = await PatientProfile.get_or_none(user=user)

    return success_response(
        {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "name": user.name,
            "role": user.role,
            "birth_date": str(user.birth_date) if user.birth_date else None,
            "gender": user.gender,
            "phone": user.phone,
            "font_size_mode": user.font_size_mode,
            "patient_profile": {
                "height_cm": float(profile.height_cm) if profile and profile.height_cm is not None else None,
                "weight_kg": float(profile.weight_kg) if profile and profile.weight_kg is not None else None,
                "allergy_details": profile.allergy_details if profile else None,
                "disease_details": profile.disease_details if profile else None,
            }
            if profile
            else None,
        }
    )


@router.patch("/me")
async def update_me(req: UserUpdateRequest, user: User = Depends(get_current_user)):
    update_data = req.model_dump(exclude_unset=True)

    user_fields = {k: v for k, v in update_data.items() if k not in _PATIENT_PROFILE_FIELDS}
    profile_fields = {k: v for k, v in update_data.items() if k in _PATIENT_PROFILE_FIELDS}

    if user_fields:
        for field, value in user_fields.items():
            setattr(user, field, value)
        await user.save()

    if profile_fields and user.role == "PATIENT":
        profile = await PatientProfile.get_or_none(user=user)
        if profile:
            for field, value in profile_fields.items():
                setattr(profile, field, value)
            await profile.save()

    return success_response({"message": "정보가 수정되었습니다."})
