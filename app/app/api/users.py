from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from tortoise.expressions import Q

from app.core.deps import get_acting_patient, get_current_user, security_scheme
from app.core.rate_limit import limiter
from app.core.redis import get_state_redis
from app.core.response import error_response, success_response
from app.core.security import decode_token, verify_password
from app.models.caregiver_patient import CaregiverPatientMapping
from app.models.patient_profile import PatientProfile
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import DeleteAccountRequest, UserUpdateRequest
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/users", tags=["users"])

_PATIENT_PROFILE_FIELDS = {"height_cm", "weight_kg", "has_allergy", "allergy_details", "has_disease", "disease_details"}


@router.get("/me")
async def get_me(actors: tuple[User, User | None] = Depends(get_acting_patient)):
    current_user, patient = actors
    target_user = patient or current_user

    profile = None
    if target_user.role == "PATIENT":
        profile = await PatientProfile.get_or_none(user=target_user)

    response_data = {
        "id": target_user.id,
        "name": target_user.name,
        "nickname": target_user.nickname,
        "role": target_user.role,
        "birth_date": str(target_user.birth_date) if target_user.birth_date else None,
        "gender": target_user.gender,
        "font_size_mode": target_user.font_size_mode,
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

    if patient is None:
        # 본인 모드: 민감 정보 포함
        response_data["email"] = target_user.email
        response_data["has_password"] = target_user.password_hash is not None
        response_data["phone"] = target_user.phone
    else:
        # 대리 모드: 민감 정보 제외 + 플래그
        response_data["is_proxy_view"] = True
        response_data["guardian_name"] = current_user.name

    return success_response(response_data)


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
@limiter.limit("10/hour")
async def delete_me(
    request: Request,
    req: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    if user.password_hash:
        if not req.password or not verify_password(req.password, user.password_hash):
            return error_response("비밀번호가 올바르지 않습니다.")
    else:
        if not req.confirm_email or req.confirm_email != user.email:
            return error_response("이메일이 일치하지 않습니다.")

    # 활성 보호자-환자 매핑을 REVOKED로 전환하고 상대방에게 알림 발송
    active_mappings = await CaregiverPatientMapping.filter(
        Q(caregiver=user) | Q(patient=user),
        status="APPROVED",
    ).prefetch_related("caregiver", "patient")

    for mapping in active_mappings:
        mapping.status = "REVOKED"
        await mapping.save()
        counterpart = mapping.patient if mapping.caregiver_id == user.id else mapping.caregiver
        await create_notification(
            user_id=counterpart.id,
            notification_type="CAREGIVER",
            title=f"{user.name}님이 탈퇴하여 연결이 해제되었습니다.",
        )

    # 현재 access token blacklist + 모든 refresh token revoke
    payload = decode_token(credentials.credentials)
    jti = payload.get("jti") if payload else None
    if jti:
        redis = await get_state_redis()
        remaining_ttl = max(1, int(payload["exp"] - datetime.now(UTC).timestamp()))
        await redis.setex(f"blacklist:{jti}", remaining_ttl, "1")
    await RefreshToken.filter(user_id=user.id, revoked=False).update(revoked=True)

    user.deleted_at = datetime.now(UTC)
    await user.save()
    return success_response({"message": "계정이 삭제되었습니다."})
