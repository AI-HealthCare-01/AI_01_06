from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.response import error_response, success_response
from app.core.security import verify_password
from app.models.patient_profile import PatientProfile
from app.models.user import User
from app.schemas.user import UserUpdateRequest

router = APIRouter(prefix="/api/users", tags=["users"])

_PATIENT_PROFILE_FIELDS = {"height_cm", "weight_kg", "has_allergy", "allergy_details", "has_disease", "disease_details"}


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
            "has_password": user.password_hash is not None,
            "birth_date": str(user.birth_date) if user.birth_date else None,
            "gender": user.gender,
            "phone": user.phone,
            "font_size_mode": user.font_size_mode,
            "patient_profile": {
                "height_cm": float(profile.height_cm) if profile and profile.height_cm is not None else None,
                "weight_kg": float(profile.weight_kg) if profile and profile.weight_kg is not None else None,
                "has_allergy": profile.has_allergy if profile else False,
                "allergy_details": profile.allergy_details if profile else None,
                "has_disease": profile.has_disease if profile else False,
                "disease_details": profile.disease_details if profile else None,
            }
            if profile
            else None,
        }
    )


@router.patch("/me")
@limiter.limit("10/minute")
async def update_me(request: Request, req: UserUpdateRequest, user: User = Depends(get_current_user)):
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
            if profile_fields.get("has_allergy") is False:
                profile_fields["allergy_details"] = None
            if profile_fields.get("has_disease") is False:
                profile_fields["disease_details"] = None

            for field, value in profile_fields.items():
                setattr(profile, field, value)
            await profile.save()

    return success_response({"message": "정보가 수정되었습니다."})


@router.delete("/me")
@limiter.limit("3/hour")
async def delete_me(
    request: Request,
    user: User = Depends(get_current_user),
    password: str | None = Query(default=None, description="로컬 계정 비밀번호 확인"),
    confirm_email: str | None = Query(default=None, description="소셜 계정 이메일 확인"),
):
    if user.password_hash:
        if not password or not verify_password(password, user.password_hash):
            return error_response("비밀번호가 올바르지 않습니다.")
    else:
        if not confirm_email or confirm_email != user.email:
            return error_response("이메일이 일치하지 않습니다.")

    user.deleted_at = datetime.now(UTC)
    await user.save()
    return success_response({"message": "계정이 삭제되었습니다."})
