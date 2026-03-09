from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from app.core.deps import get_current_user
from app.core.response import error_response, success_response
from app.models.caregiver_patient import CaregiverPatientMapping
from app.models.user import User

router = APIRouter(prefix="/api/caregivers", tags=["caregivers"])


class CaregiverRequestBody(BaseModel):
    patient_nickname: str


class MappingStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("APPROVED", "REJECTED"):
            raise ValueError("status는 APPROVED 또는 REJECTED여야 합니다.")
        return v


@router.post("/request")
async def request_link(req: CaregiverRequestBody, user: User = Depends(get_current_user)):
    if user.role != "GUARDIAN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="보호자만 연결 요청을 할 수 있습니다.")

    patient = await User.filter(nickname=req.patient_nickname, role="PATIENT", deleted_at__isnull=True).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 닉네임의 환자를 찾을 수 없습니다.")

    if patient.id == user.id:
        return error_response("자기 자신에게 요청할 수 없습니다.")

    existing = await CaregiverPatientMapping.filter(caregiver=user, patient=patient).first()
    if existing and existing.status in ("PENDING", "APPROVED"):
        return error_response("이미 연결 요청이 존재합니다.")

    mapping = await CaregiverPatientMapping.create(caregiver=user, patient=patient)
    return success_response({"id": mapping.id, "status": mapping.status})


@router.get("/requests")
async def list_requests(user: User = Depends(get_current_user)):
    if user.role != "PATIENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="환자만 요청 목록을 조회할 수 있습니다.")

    mappings = await CaregiverPatientMapping.filter(patient=user, status="PENDING").prefetch_related("caregiver")
    result = [
        {"id": m.id, "caregiver_nickname": m.caregiver.nickname, "requested_at": str(m.requested_at)} for m in mappings
    ]
    return success_response(result)


@router.patch("/requests/{mapping_id}")
async def respond_to_request(mapping_id: int, req: MappingStatusUpdate, user: User = Depends(get_current_user)):
    if user.role != "PATIENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="환자만 요청에 응답할 수 있습니다.")

    mapping = await CaregiverPatientMapping.get_or_none(id=mapping_id, patient=user, status="PENDING")
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="요청을 찾을 수 없습니다.")

    mapping.status = req.status
    if req.status == "APPROVED":
        mapping.accepted_at = datetime.now(UTC)
    await mapping.save()
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
    return success_response({"message": "연결이 해제되었습니다."})


@router.get("/patients")
async def list_patients(user: User = Depends(get_current_user)):
    if user.role != "GUARDIAN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="보호자만 조회할 수 있습니다.")

    mappings = await CaregiverPatientMapping.filter(caregiver=user, status="APPROVED").prefetch_related("patient")
    result = [{"id": m.patient.id, "nickname": m.patient.nickname, "name": m.patient.name} for m in mappings]
    return success_response(result)


@router.get("/my-caregivers")
async def list_my_caregivers(user: User = Depends(get_current_user)):
    if user.role != "PATIENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="환자만 조회할 수 있습니다.")

    mappings = await CaregiverPatientMapping.filter(patient=user, status="APPROVED").prefetch_related("caregiver")
    result = [{"id": m.caregiver.id, "nickname": m.caregiver.nickname, "name": m.caregiver.name} for m in mappings]
    return success_response(result)
