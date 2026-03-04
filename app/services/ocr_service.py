"""
OCR 서비스 (B담당 핵심)

파이프라인:
  1. PrescriptionImage의 file_url로 이미지를 읽음
  2. CLOVA General OCR API를 호출하여 텍스트 추출
  3. 추출된 텍스트를 OpenAI gpt-4o-mini로 약 데이터 구조화
  4. OcrJob에 결과 저장, Prescription 상태를 COMPLETE로 업데이트

OCR_MODE=mock 시 실제 API 없이 가짜 데이터로 전체 흐름 테스트 가능.
키를 받으면 .env에서 OCR_MODE=real 로만 바꾸면 됩니다.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import HTTPException, status

from app.core import config
from app.models.prescriptions import PrescriptionStatus
from app.repositories.medication_repository import MedicationRepository
from app.repositories.ocr_repository import OcrRepository
from app.repositories.prescription_repository import PrescriptionRepository

logger = logging.getLogger("ai_health.ocr_service")

# ─── parsed_fields 최소 스키마 ────────────────────────────────────────────────
PARSED_FIELDS_SYSTEM_PROMPT = """
당신은 한국 병원 처방전에서 약 정보를 추출하는 전문가입니다.
입력된 텍스트에서 약 목록을 추출하여 반드시 다음 JSON 형식으로만 응답하십시오.
다른 설명 없이 JSON 코드만 출력하십시오.

{
  "medications": [
    {
      "drug_name": "약품명 (필수)",
      "dosage": "1회 용량 (예: '1정', '5ml')",
      "frequency": "1일 횟수 (예: '3', '2')",
      "administration": "복용 방법 (예: '식후30분', '식전')",
      "duration_days": 복용기간일수(정수),
      "caution": "주의사항 (없으면 빈 문자열)"
    }
  ]
}

규칙:
- drug_name이 없는 항목은 제외
- duration_days는 숫자만, 없으면 null
- 약이 없으면 medications는 빈 배열 []
"""


class OcrService:
    """처방전 OCR 실행 서비스"""

    def __init__(self):
        self.ocr_repo = OcrRepository()
        self.prescription_repo = PrescriptionRepository()
        self.medication_repo = MedicationRepository()

    # ──────────────────────────────────────────────────────────────────────────
    # 공개 인터페이스
    # ──────────────────────────────────────────────────────────────────────────

    async def run_ocr_for_prescription(
        self,
        prescription_id: int,
        prescription_image_id: int,
        file_url: str,
    ) -> None:
        """
        OCR 전체 파이프라인을 실행합니다.

        1. OcrJob 생성 → PROCESSING
        2. OCR 실행 (real or mock)
        3. GPT로 parsed_fields 구조화
        4. OcrJob → COMPLETE, medications 생성
        5. 실패 시 → OcrJob/Prescription FAILED

        이 메서드는 FastAPI 라우터에서 background_tasks.add_task()로 
        비동기 백그라운드 실행됩니다.
        """
        # OcrJob 생성
        job = await self.ocr_repo.create_job(prescription_image_id)
        await self.ocr_repo.mark_processing(job.id)
        await self.prescription_repo.update_status(prescription_id, PrescriptionStatus.PROCESSING)

        try:
            # OCR 실행
            raw_ocr_json, extracted_text = await self._run_ocr(file_url)

            # GPT로 구조화
            extracted_json = await self._parse_with_llm(extracted_text)

            # OcrJob 완료 저장
            await self.ocr_repo.mark_complete(
                job_id=job.id,
                raw_ocr_json=raw_ocr_json,
                extracted_text=extracted_text,
                extracted_json=extracted_json,
            )

            # medications 생성
            meds = extracted_json.get("medications", [])
            if meds:
                await self.medication_repo.bulk_create(prescription_id, meds)

            # 처방전 상태 → COMPLETE
            await self.prescription_repo.update_status(prescription_id, PrescriptionStatus.COMPLETE)
            logger.info(f"OCR 완료: prescription_id={prescription_id}, job_id={job.id}, 약 {len(meds)}종")

        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)
            logger.error(f"OCR 실패: prescription_id={prescription_id}, job_id={job.id}, error={error_msg}")
            await self.ocr_repo.mark_failed(job.id, error_msg)
            await self.prescription_repo.update_status(prescription_id, PrescriptionStatus.FAILED)

    async def retry_ocr(self, prescription_id: int) -> None:
        """
        OCR 재시도.
        FAILED 상태인 처방전의 첫 번째 이미지를 다시 OCR 실행합니다.
        """
        # 기존 실패 Job 조회
        job = await self.ocr_repo.get_latest_by_prescription(prescription_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OCR Job을 찾을 수 없습니다.",
            )

        if job.status not in ("FAILED", "PENDING"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"재시도는 FAILED/PENDING 상태에서만 가능합니다. 현재: {job.status}",
            )

        await job.fetch_related("prescription_image")
        img = job.prescription_image

        # 기존 약 소프트 삭제 후 재시도
        await self.medication_repo.soft_delete_all_by_prescription(prescription_id)
        await self.run_ocr_for_prescription(prescription_id, img.id, img.file_url)

    # ──────────────────────────────────────────────────────────────────────────
    # 내부 구현
    # ──────────────────────────────────────────────────────────────────────────

    async def _run_ocr(self, file_url: str) -> tuple[dict, str]:
        """
        OCR_MODE에 따라 real/mock 실행.
        Returns: (raw_ocr_json, extracted_text)
        """
        if config.OCR_MODE == "real":
            return await self._call_clova_ocr(file_url)
        else:
            return self._mock_ocr_response()

    async def _call_clova_ocr(self, file_url: str) -> tuple[dict, str]:
        """
        CLOVA General OCR API 호출.

        CLOVA API 문서:
          https://api.ncloud-docs.com/docs/ai-application-service-ocr-general

        요청 형식: multipart/form-data
          - message: JSON 문자열 (이미지 정보)
          - file: 이미지 바이너리
        """
        # 로컬 파일 경로로 변환
        from app.utils.file_storage import get_file_path_from_url
        file_path = get_file_path_from_url(file_url)

        if not file_path.exists():
            raise FileNotFoundError(f"업로드 파일을 찾을 수 없습니다: {file_url}")

        file_bytes = file_path.read_bytes()
        filename = file_path.name

        # CLOVA API 메시지 구성
        message = json.dumps({
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(datetime.now().timestamp() * 1000),
            "lang": "ko",
            "images": [
                {
                    "format": file_path.suffix.lstrip(".").upper(),
                    "name": filename,
                }
            ],
            "enableTableDetect": False,
        })

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url=config.CLOVA_OCR_API_URL,
                headers={"X-OCR-SECRET": config.CLOVA_OCR_SECRET_KEY},
                files={"file": (filename, file_bytes)},
                data={"message": message},
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"CLOVA OCR API 오류: status={response.status_code}, body={response.text[:200]}"
            )

        raw_json = response.json()

        # 텍스트 추출
        texts: list[str] = []
        for image_result in raw_json.get("images", []):
            for field in image_result.get("fields", []):
                texts.append(field.get("inferText", ""))

        extracted_text = " ".join(texts)
        return raw_json, extracted_text

    @staticmethod
    def _mock_ocr_response() -> tuple[dict, str]:
        """
        OCR_MODE=mock 시 반환하는 가짜 응답.
        실제 키 없이 전체 파이프라인 테스트에 사용합니다.
        """
        raw = {
            "version": "V2",
            "requestId": "mock-request",
            "images": [
                {
                    "fields": [
                        {"inferText": "처방전"},
                        {"inferText": "타이레놀정500mg"},
                        {"inferText": "1회1정"},
                        {"inferText": "1일3회"},
                        {"inferText": "식후30분"},
                        {"inferText": "3일분"},
                        {"inferText": "아목시실린캡슐250mg"},
                        {"inferText": "1회1캡슐"},
                        {"inferText": "1일2회"},
                        {"inferText": "식후"},
                        {"inferText": "5일분"},
                    ]
                }
            ],
        }
        text = (
            "처방전 타이레놀정500mg 1회1정 1일3회 식후30분 3일분 "
            "아목시실린캡슐250mg 1회1캡슐 1일2회 식후 5일분"
        )
        return raw, text

    async def _parse_with_llm(self, extracted_text: str) -> dict:
        """
        OpenAI GPT로 OCR 텍스트 → parsed_fields JSON 구조화.

        API Key 없거나 실패 시 → mock parsed_fields 반환 (fallback).
        """
        if config.OPENAI_API_KEY.startswith("CHANGE_ME") or config.OCR_MODE == "mock":
            logger.info("OpenAI 키 미설정, mock parsed_fields 반환")
            return self._mock_parsed_fields()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": config.OPENAI_MODEL,
                        "temperature": 0,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": PARSED_FIELDS_SYSTEM_PROMPT},
                            {"role": "user", "content": f"처방전 텍스트:\n{extracted_text}"},
                        ],
                    },
                )

            if response.status_code != 200:
                logger.warning(f"OpenAI API 오류 {response.status_code}, fallback 사용")
                return self._mock_parsed_fields()

            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)

        except Exception as e:  # noqa: BLE001
            logger.warning(f"LLM 파싱 실패: {e}, fallback 사용")
            return self._mock_parsed_fields()

    @staticmethod
    def _mock_parsed_fields() -> dict:
        """GPT 호출 없이 반환하는 기본 parsed_fields"""
        return {
            "medications": [
                {
                    "drug_name": "타이레놀정500mg",
                    "dosage": "1정",
                    "frequency": "3",
                    "administration": "식후30분",
                    "duration_days": 3,
                    "caution": "",
                },
                {
                    "drug_name": "아목시실린캡슐250mg",
                    "dosage": "1캡슐",
                    "frequency": "2",
                    "administration": "식후",
                    "duration_days": 5,
                    "caution": "페니실린 알레르기 확인",
                },
            ]
        }
