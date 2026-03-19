from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from tortoise.exceptions import IntegrityError

from app import config
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.response import success_response
from app.models.caregiver_patient import CaregiverPatientMapping
from app.models.user import User
from app.services.invite_service import consume_invite_token, create_invite_token, get_invite_data
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/caregivers", tags=["caregivers"])

# 초대자와 수락자는 반드시 서로 반대 role이어야 함
_OPPOSITE_ROLE: dict[str, str] = {"PATIENT": "GUARDIAN", "GUARDIAN": "PATIENT"}


@router.post("/invite")
@limiter.limit("10/minute")
async def create_invite(request: Request, user: User = Depends(get_current_user)):
    token = await create_invite_token(user.id, user.role)
    invite_url = f"{config.FRONTEND_URL}/invite/{token}"
    return success_response({"token": token, "invite_url": invite_url})


@router.get("/invite/{token}")
@limiter.limit("30/minute")
async def validate_invite(request: Request, token: str, user: User = Depends(get_current_user)):
    data = await get_invite_data(token)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="초대가 만료되었거나 존재하지 않습니다.")
    inviter = await User.get_or_none(id=data["user_id"], deleted_at__isnull=True)
    if not inviter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="초대자를 찾을 수 없습니다.")
    return success_response(
        {
            "inviter_name": inviter.name,
            "inviter_nickname": inviter.nickname,
            "inviter_role": data["role"],
        }
    )


@router.post("/invite/{token}/accept")
@limiter.limit("20/minute")
async def accept_invite(request: Request, token: str, user: User = Depends(get_current_user)):
    data = await get_invite_data(token)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="초대가 만료되었거나 존재하지 않습니다.")

    inviter = await User.get_or_none(id=data["user_id"], deleted_at__isnull=True)
    if not inviter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="초대자를 찾을 수 없습니다.")

    # 자기 자신 수락 방지
    if inviter.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="자기 자신의 초대를 수락할 수 없습니다.")

    # role 교차 검증: 초대자와 수락자는 반드시 서로 다른 role이어야 함
    expected_role = _OPPOSITE_ROLE.get(data["role"])
    if user.role != expected_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"이 초대는 {expected_role} 역할의 사용자만 수락할 수 있습니다.",
        )

    # 역할에 따라 caregiver/patient 결정
    if data["role"] == "PATIENT":
        patient, caregiver = inviter, user
    else:
        patient, caregiver = user, inviter

    # 토큰 먼저 소비 (TOCTOU 방지: 동시 요청에서 한 요청만 처리되도록 원자적으로 소비)
    consumed = await consume_invite_token(token)
    if not consumed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="초대가 만료되었거나 존재하지 않습니다.")

    # REVOKED 매핑이 존재하면 재활성화, 없으면 새로 생성
    existing = await CaregiverPatientMapping.get_or_none(caregiver=caregiver, patient=patient)
    if existing:
        if existing.status != "REVOKED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 연결된 관계입니다.")
        existing.status = "APPROVED"
        existing.accepted_at = datetime.now(UTC)
        await existing.save()
        await create_notification(
            user_id=inviter.id,
            notification_type="CAREGIVER",
            title=f"{user.name}님이 연결을 수락했습니다.",
        )
        return success_response({"id": existing.id, "status": existing.status})

    try:
        mapping = await CaregiverPatientMapping.create(
            caregiver=caregiver,
            patient=patient,
            status="APPROVED",
            accepted_at=datetime.now(UTC),
        )
    except IntegrityError as e:
        # 동시 요청 race condition 안전망
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 연결된 관계입니다.") from e
    await create_notification(
        user_id=inviter.id,
        notification_type="CAREGIVER",
        title=f"{user.name}님이 연결을 수락했습니다.",
    )
    return success_response({"id": mapping.id, "status": mapping.status})


@router.delete("/{mapping_id}")
async def revoke_link(mapping_id: int, user: User = Depends(get_current_user)):
    mapping = await CaregiverPatientMapping.get_or_none(id=mapping_id, status="APPROVED")
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="연결 정보를 찾을 수 없습니다.")

    await mapping.fetch_related("caregiver", "patient")
    if user.id not in (mapping.caregiver.id, mapping.patient.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")

    mapping.status = "REVOKED"
    await mapping.save()

    if user.id == mapping.caregiver.id:
        counterpart = mapping.patient
    else:
        counterpart = mapping.caregiver

    await create_notification(
        user_id=counterpart.id,
        notification_type="CAREGIVER",
        title=f"{user.name}님이 연결을 해제했습니다.",
    )
    return success_response({"message": "연결이 해제되었습니다."})


@router.get("/patients")
async def list_patients(user: User = Depends(get_current_user)):
    if user.role != "GUARDIAN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="보호자만 조회할 수 있습니다.")

    mappings = await CaregiverPatientMapping.filter(caregiver=user, status="APPROVED").prefetch_related("patient")
    result = [
        {"mapping_id": m.id, "id": m.patient.id, "nickname": m.patient.nickname, "name": m.patient.name}
        for m in mappings
    ]
    return success_response(result)


@router.get("/my-caregivers")
async def list_my_caregivers(user: User = Depends(get_current_user)):
    if user.role != "PATIENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="환자만 조회할 수 있습니다.")

    mappings = await CaregiverPatientMapping.filter(patient=user, status="APPROVED").prefetch_related("caregiver")
    result = [
        {"mapping_id": m.id, "id": m.caregiver.id, "nickname": m.caregiver.nickname, "name": m.caregiver.name}
        for m in mappings
    ]
    return success_response(result)
