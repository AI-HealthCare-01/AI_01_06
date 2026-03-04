"""
처방전 서비스 (B담당)

업로드, 조회, OCR 보정, 재시도 흐름을 관장합니다.
"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

from app.dtos.prescriptions import (
    MedicationUpdateRequest,
    OcrCorrectionRequest,
    PrescriptionCreateRequest,
)
from app.models.medications import Medication
from app.models.ocr_jobs import OcrJob
from app.models.prescriptions import Prescription, PrescriptionStatus
from app.repositories.medication_repository import MedicationRepository
from app.repositories.ocr_repository import OcrRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.utils.file_storage import save_upload_file


class PrescriptionService:
    """처방전 비즈니스 로직 전담"""

    def __init__(self):
        self.prescription_repo = PrescriptionRepository()
        self.ocr_repo = OcrRepository()
        self.medication_repo = MedicationRepository()

    # ─── 업로드 ──────────────────────────────────────────────────────────────

    async def upload_prescription(
        self,
        uploader_user_id: int,
        data: PrescriptionCreateRequest,
        file: UploadFile,
    ) -> tuple[Prescription, int, str]:
        """
        처방전 이미지를 업로드하고 Prescription + PrescriptionImage + OcrJob을 생성합니다.

        Returns:
            (prescription, image_id, file_url)
            → 라우터가 이를 받아서 BackgroundTask로 OCR을 실행합니다.
        """
        from tortoise.transactions import in_transaction

        # 1. 파일 저장
        file_url, mime_type = await save_upload_file(file, uploader_user_id)

        async with in_transaction():
            # 2. Prescription 생성
            prescription = await self.prescription_repo.create(
                patient_id=data.patient_id,
                created_by_user_id=uploader_user_id,
                hospital_name=data.hospital_name,
                doctor_name=data.doctor_name,
                prescription_date=data.prescription_date,
                diagnosis=data.diagnosis,
            )

            # 3. PrescriptionImage 생성
            image = await self.prescription_repo.create_image(
                prescription_id=prescription.id,
                file_url=file_url,
                mime_type=mime_type,
            )

        return prescription, image.id, file_url

    # ─── 조회 ──────────────────────────────────────────────────────────────

    async def get_prescription(self, prescription_id: int, requester_user_id: int) -> Prescription:
        """처방전 1건 조회 (접근 권한 확인 포함)"""
        prescription = await self.prescription_repo.get_by_id(prescription_id)
        self._assert_exists(prescription, prescription_id)
        self._assert_access(prescription, requester_user_id)
        return prescription

    async def list_prescriptions(self, patient_id: int) -> list[Prescription]:
        """환자의 처방전 목록"""
        return await self.prescription_repo.get_list_by_patient(patient_id)

    async def get_ocr_result(self, prescription_id: int, requester_user_id: int) -> OcrJob:
        """OCR 결과 조회"""
        prescription = await self.prescription_repo.get_by_id(prescription_id)
        self._assert_exists(prescription, prescription_id)
        self._assert_access(prescription, requester_user_id)

        job = await self.ocr_repo.get_latest_by_prescription(prescription_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OCR 결과를 찾을 수 없습니다. 먼저 처방전을 업로드하세요.",
            )
        return job

    async def get_medications(self, prescription_id: int, requester_user_id: int) -> list[Medication]:
        """약 목록 조회"""
        prescription = await self.prescription_repo.get_by_id(prescription_id)
        self._assert_exists(prescription, prescription_id)
        self._assert_access(prescription, requester_user_id)
        return await self.medication_repo.get_active_by_prescription(prescription_id)

    # ─── OCR 보정 ──────────────────────────────────────────────────────────

    async def correct_ocr(
        self,
        prescription_id: int,
        requester_user_id: int,
        data: OcrCorrectionRequest,
    ) -> OcrJob:
        """
        사용자 보정.

        - extracted_json을 덮어씁니다.
        - data.regenerate=True이면 기존 medications를 소프트삭제하고 재생성합니다.
        """
        prescription = await self.prescription_repo.get_by_id(prescription_id)
        self._assert_exists(prescription, prescription_id)
        self._assert_access(prescription, requester_user_id)

        job = await self.ocr_repo.get_latest_by_prescription(prescription_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="보정할 OCR 결과가 없습니다.",
            )

        # extracted_json 업데이트
        await self.ocr_repo.update_extracted_json(job.id, data.extracted_json)

        # 재생성 요청 시
        if data.regenerate:
            await self.medication_repo.soft_delete_all_by_prescription(prescription_id)
            meds = data.extracted_json.get("medications", [])
            if meds:
                await self.medication_repo.bulk_create(prescription_id, meds)

        # 최신 상태 반환
        updated_job = await self.ocr_repo.get_by_id(job.id)
        return updated_job  # type: ignore[return-value]

    # ─── 약 수정 ──────────────────────────────────────────────────────────

    async def update_medication(
        self,
        prescription_id: int,
        medication_id: int,
        requester_user_id: int,
        data: MedicationUpdateRequest,
    ) -> Medication:
        """약 1건 수정"""
        prescription = await self.prescription_repo.get_by_id(prescription_id)
        self._assert_exists(prescription, prescription_id)
        self._assert_access(prescription, requester_user_id)

        medication = await self.medication_repo.get_by_id(medication_id)
        if not medication or medication.prescription_id != prescription_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="약 정보를 찾을 수 없습니다.",
            )

        update_data = data.model_dump(exclude_none=True)
        return await self.medication_repo.update(medication, update_data)

    # ─── 내부 헬퍼 ────────────────────────────────────────────────────────

    @staticmethod
    def _assert_exists(prescription: Prescription | None, prescription_id: int) -> None:
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"처방전 {prescription_id}을(를) 찾을 수 없습니다.",
            )

    @staticmethod
    def _assert_access(prescription: Prescription, requester_user_id: int) -> None:
        """
        접근 제어:
        - 본인(patient) 또는 업로드한 사람(created_by_user_id)만 접근 가능.
        - A담당이 ADMIN/CAREGIVER 역할 미들웨어를 추가하면 여기서 role도 확인합니다.
        """
        allowed_ids = {prescription.patient_id, prescription.created_by_user_id}
        if requester_user_id not in allowed_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 처방전에 접근할 권한이 없습니다.",
            )
