"""
처방전·OCR·약 API 라우터 (B담당)

모든 엔드포인트는 JWT 인증 필요 (get_request_user).
OCR은 BackgroundTask로 비동기 실행됩니다.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.prescriptions import (
    MedicationResponse,
    MedicationUpdateRequest,
    OcrCorrectionRequest,
    OcrResultResponse,
    PrescriptionCreateRequest,
    PrescriptionResponse,
)
from app.models.users import User
from app.services.ocr_service import OcrService
from app.services.prescription_service import PrescriptionService

prescription_router = APIRouter(prefix="/prescriptions", tags=["prescriptions (B담당)"])


# ═══════════════════════════════════════════════════════════════════════════════
# 처방전 업로드
# ═══════════════════════════════════════════════════════════════════════════════

@prescription_router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="처방전 이미지 업로드 + OCR 시작",
    description="""
처방전 이미지를 업로드합니다. OCR은 백그라운드에서 비동기로 실행됩니다.

- 즉시 `202 Accepted` + prescription_id 반환
- OCR 완료 후 GET /prescriptions/{id}/ocr 로 결과 조회
- `OCR_MODE=mock`이면 실제 API 없이도 테스트 가능

**Content-Type: multipart/form-data**
""",
)
async def upload_prescription(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_request_user)],
    file: UploadFile = File(..., description="처방전 이미지 (JPEG/PNG/PDF)"),
    patient_id: int = Form(..., description="복약 환자 user_id"),
    hospital_name: str | None = Form(None, description="병원명"),
    doctor_name: str | None = Form(None, description="의사명"),
    prescription_date: str | None = Form(None, description="처방일 (YYYY-MM-DD)"),
    diagnosis: str | None = Form(None, description="진단명"),
) -> Response:
    from datetime import date

    # Form → DTO 변환
    parsed_date: date | None = None
    if prescription_date:
        try:
            parsed_date = date.fromisoformat(prescription_date)
        except ValueError:
            pass

    dto = PrescriptionCreateRequest(
        patient_id=patient_id,
        hospital_name=hospital_name,
        doctor_name=doctor_name,
        prescription_date=parsed_date,
        diagnosis=diagnosis,
    )

    svc = PrescriptionService()
    prescription, image_id, file_url = await svc.upload_prescription(
        uploader_user_id=current_user.id,
        data=dto,
        file=file,
    )

    # OCR은 백그라운드에서 실행 (응답은 즉시 반환)
    ocr_svc = OcrService()
    background_tasks.add_task(
        ocr_svc.run_ocr_for_prescription,
        prescription.id,
        image_id,
        file_url,
    )

    return Response(
        content={
            "success": True,
            "message": "처방전이 업로드되었습니다. OCR을 백그라운드에서 실행 중입니다.",
            "data": {
                "prescription_id": prescription.id,
                "status": prescription.verification_status,
            },
        },
        status_code=status.HTTP_202_ACCEPTED,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 처방전 목록·상세 조회
# ═══════════════════════════════════════════════════════════════════════════════

@prescription_router.get(
    "",
    summary="내 처방전 목록",
    response_model=list[PrescriptionResponse],
)
async def list_my_prescriptions(
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    svc = PrescriptionService()
    prescriptions = await svc.list_prescriptions(patient_id=current_user.id)
    data = [PrescriptionResponse.model_validate(p).model_dump() for p in prescriptions]
    return Response(
        content={"success": True, "data": data},
        status_code=status.HTTP_200_OK,
    )


@prescription_router.get(
    "/{prescription_id}",
    summary="처방전 상세 조회 (이미지 URL + 약 목록 + OCR 상태)",
)
async def get_prescription_detail(
    prescription_id: int,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    svc = PrescriptionService()

    prescription = await svc.get_prescription(prescription_id, current_user.id)
    images = await svc.prescription_repo.get_images_by_prescription(prescription_id)
    medications = await svc.medication_repo.get_active_by_prescription(prescription_id)

    return Response(
        content={
            "success": True,
            "data": {
                **PrescriptionResponse.model_validate(prescription).model_dump(),
                "image_urls": [img.file_url for img in images],
                "medications": [MedicationResponse.model_validate(m).model_dump() for m in medications],
            },
        },
        status_code=status.HTTP_200_OK,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# OCR 결과 조회 + 보정
# ═══════════════════════════════════════════════════════════════════════════════

@prescription_router.get(
    "/{prescription_id}/ocr",
    summary="OCR 결과 조회 (추출 텍스트 + 구조화 약 데이터)",
    response_model=OcrResultResponse,
)
async def get_ocr_result(
    prescription_id: int,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    svc = PrescriptionService()
    job = await svc.get_ocr_result(prescription_id, current_user.id)
    return Response(
        content={"success": True, "data": OcrResultResponse.model_validate(job).model_dump()},
        status_code=status.HTTP_200_OK,
    )


@prescription_router.put(
    "/{prescription_id}/ocr",
    summary="OCR 결과 보정 저장 (사용자 수동 수정)",
    description="""
OCR 결과(extracted_json)를 사용자가 직접 수정합니다.

- `regenerate=true` (기본값): 기존 medications 소프트삭제 후 재생성
- `regenerate=false`: extracted_json만 업데이트, 약 목록은 유지
""",
    response_model=OcrResultResponse,
)
async def correct_ocr_result(
    prescription_id: int,
    data: OcrCorrectionRequest,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    svc = PrescriptionService()
    job = await svc.correct_ocr(prescription_id, current_user.id, data)
    return Response(
        content={
            "success": True,
            "message": "OCR 결과가 보정되었습니다.",
            "data": OcrResultResponse.model_validate(job).model_dump(),
        },
        status_code=status.HTTP_200_OK,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# OCR 재시도
# ═══════════════════════════════════════════════════════════════════════════════

@prescription_router.post(
    "/{prescription_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    summary="OCR 재시도 (FAILED 상태 처방전)",
    description="OCR이 실패한 처방전을 다시 시도합니다. FAILED 또는 PENDING 상태에서만 가능합니다.",
)
async def retry_ocr(
    prescription_id: int,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    # 접근 권한 확인
    svc = PrescriptionService()
    await svc.get_prescription(prescription_id, current_user.id)

    # 백그라운드 재시도
    ocr_svc = OcrService()
    background_tasks.add_task(ocr_svc.retry_ocr, prescription_id)

    return Response(
        content={
            "success": True,
            "message": "OCR 재시도를 시작했습니다.",
            "data": {"prescription_id": prescription_id},
        },
        status_code=status.HTTP_202_ACCEPTED,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 약 목록·수정
# ═══════════════════════════════════════════════════════════════════════════════

@prescription_router.get(
    "/{prescription_id}/medications",
    summary="약 목록 조회",
    response_model=list[MedicationResponse],
)
async def get_medications(
    prescription_id: int,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    svc = PrescriptionService()
    medications = await svc.get_medications(prescription_id, current_user.id)
    data = [MedicationResponse.model_validate(m).model_dump() for m in medications]
    return Response(
        content={"success": True, "data": data},
        status_code=status.HTTP_200_OK,
    )


@prescription_router.put(
    "/{prescription_id}/medications/{medication_id}",
    summary="약 수정 (개별 수동 수정)",
    response_model=MedicationResponse,
)
async def update_medication(
    prescription_id: int,
    medication_id: int,
    data: MedicationUpdateRequest,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    svc = PrescriptionService()
    medication = await svc.update_medication(
        prescription_id=prescription_id,
        medication_id=medication_id,
        requester_user_id=current_user.id,
        data=data,
    )
    return Response(
        content={
            "success": True,
            "message": "약 정보가 수정되었습니다.",
            "data": MedicationResponse.model_validate(medication).model_dump(),
        },
        status_code=status.HTTP_200_OK,
    )
