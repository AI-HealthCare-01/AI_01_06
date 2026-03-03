"""
PRESCRIPTION / OCR / MEDICATION 도메인 라우터.

기준: docs/dev/api_spec.md
  POST   /api/prescriptions
  GET    /api/prescriptions
  GET    /api/prescriptions/{prescription_id}
  DELETE /api/prescriptions/{prescription_id}
  GET    /api/prescriptions/{prescription_id}/ocr
  PUT    /api/prescriptions/{prescription_id}/ocr
  GET    /api/prescriptions/{prescription_id}/medications
  GET    /api/medications/{medication_id}
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.medication import MedicationDetailResponse
from app.dtos.prescription import (
    OcrResultResponse,
    OcrUpdateRequest,
    PrescriptionDetailResponse,
)
from app.models.users import User
from app.repositories.medical_repository import MedicationRepository, OcrRepository, PrescriptionRepository

prescription_router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])
medication_router = APIRouter(prefix="/medications", tags=["medications"])

_pres_repo = PrescriptionRepository()
_ocr_repo = OcrRepository()
_med_repo = MedicationRepository()


@prescription_router.post("", status_code=status.HTTP_201_CREATED)
async def upload_prescription(
    file: UploadFile,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-OCR-001: 처방전 이미지 업로드."""
    prescription = await _pres_repo.create(
        patient_id=user.id,
        created_by_user_id=user.id,
    )
    # 파일 저장 및 OCR 연동은 ai_worker에서 처리 (비동기)
    return Response(
        content={"prescription_id": prescription.id, "status": "DRAFT"},
        status_code=status.HTTP_201_CREATED,
    )


@prescription_router.get("", status_code=status.HTTP_200_OK)
async def list_prescriptions(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    prescriptions = await _pres_repo.list_by_patient(user.id)
    data = [PrescriptionDetailResponse.model_validate(p).model_dump(mode="json") for p in prescriptions]
    return Response(content={"prescriptions": data, "total": len(data)}, status_code=status.HTTP_200_OK)


@prescription_router.get("/{prescription_id}", status_code=status.HTTP_200_OK)
async def get_prescription(
    prescription_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    p = await _pres_repo.get_by_id(prescription_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")
    return Response(
        content=PrescriptionDetailResponse.model_validate(p).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


@prescription_router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription(
    prescription_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    p = await _pres_repo.get_by_id(prescription_id)
    if not p or p.patient_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")
    await _pres_repo.delete(p)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


@prescription_router.get("/{prescription_id}/ocr", status_code=status.HTTP_200_OK)
async def get_ocr_result(
    prescription_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-OCR-004: OCR 결과 조회."""
    ocr = await _ocr_repo.get_by_prescription(prescription_id)
    if not ocr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR 결과가 없습니다.")
    return Response(
        content=OcrResultResponse.model_validate(ocr).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


@prescription_router.put("/{prescription_id}/ocr", status_code=status.HTTP_200_OK)
async def update_ocr(
    prescription_id: str,
    body: OcrUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-OCR-008: 잘못 인식된 약물명/용량 수정."""
    ocr = await _ocr_repo.get_by_prescription(prescription_id)
    if not ocr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR 결과가 없습니다.")
    await _ocr_repo.update_extracted(ocr, body.parsed_fields)
    return Response(content={"detail": "OCR 결과가 수정되었습니다."}, status_code=status.HTTP_200_OK)


@prescription_router.get("/{prescription_id}/medications", status_code=status.HTTP_200_OK)
async def list_medications_by_prescription(
    prescription_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    meds = await _med_repo.list_by_prescription(prescription_id)
    data = [MedicationDetailResponse.model_validate(m).model_dump(mode="json") for m in meds]
    return Response(content={"medications": data}, status_code=status.HTTP_200_OK)


@medication_router.get("/{medication_id}", status_code=status.HTTP_200_OK)
async def get_medication(
    medication_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    med = await _med_repo.get_by_id(medication_id)
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="약물 정보를 찾을 수 없습니다.")
    return Response(
        content=MedicationDetailResponse.model_validate(med).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )
