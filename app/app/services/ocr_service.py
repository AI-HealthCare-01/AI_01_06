import abc
import base64
import time
import uuid

import httpx

from app import config

_MED_TABLE_HEADER = "처방의약품의명칭"
_NUM_MED_COLS = 5  # 처방의약품의명칭 | 1회투여량 | 1일투여횟수 | 총투여일수 | 용법


class OcrServiceBase(abc.ABC):
    @abc.abstractmethod
    async def extract(self, image_path: str) -> dict: ...


class DummyOcrService(OcrServiceBase):
    """Stub OCR that returns sample prescription data.
    Replace with NaverOcrService for production.
    """

    async def extract(self, image_path: str) -> dict:
        return {
            "hospital_name": "서울대학교병원",
            "doctor_name": "김의사",
            "prescription_date": "2026-02-25",
            "diagnosis": "당뇨병, 고혈압",
            "medications": [
                {
                    "name": "아스피린",
                    "dosage": "100mg",
                    "frequency": "1일 1회 아침 식후",
                    "duration": "30일",
                    "instructions": "충분한 물과 함께 복용",
                },
                {
                    "name": "메트포르민",
                    "dosage": "500mg",
                    "frequency": "1일 2회 아침/저녁 식후",
                    "duration": "30일",
                    "instructions": "식사 직후 복용",
                },
            ],
        }


class NaverOcrService(OcrServiceBase):
    """Naver Clova OCR integration."""

    def __init__(self, secret: str, url: str) -> None:
        self.secret = secret
        self.url = url

    async def extract(self, image_path: str) -> dict:
        texts = await self._call_clova_api(image_path)
        return self._parse_fields(texts)

    async def _call_clova_api(self, image_path: str) -> list[str]:
        """Naver Clova OCR API 호출 후 인식된 텍스트 블록 리스트 반환."""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.rsplit(".", 1)[-1].lower()
        payload = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "lang": "ko",
            "images": [{"format": ext, "name": "prescription", "data": image_data}],
        }
        headers = {
            "X-OCR-SECRET": self.secret,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()

        fields = response.json()["images"][0].get("fields", [])
        return [f["inferText"] for f in fields if f.get("inferText")]

    def _parse_fields(self, texts: list[str]) -> dict:
        """Raw OCR 텍스트 블록을 처방전 구조화 dict로 파싱."""
        result: dict = {
            "hospital_name": None,
            "doctor_name": None,
            "prescription_date": None,
            "diagnosis": None,
            "medications": [],
        }

        field_keywords: dict[str, str] = {
            "요양기관명": "hospital_name",
            "의료기관명": "hospital_name",
            "병원명": "hospital_name",
            "처방의사성명": "doctor_name",
            "의사성명": "doctor_name",
            "처방의": "doctor_name",
            "처방일": "prescription_date",
            "처방일자": "prescription_date",
            "상병명": "diagnosis",
            "진단명": "diagnosis",
        }
        label_set = set(field_keywords.keys())
        normalized = [t.strip() for t in texts if t.strip()]

        # 약품 테이블 시작 위치 탐색
        med_table_start: int | None = None
        for i, text in enumerate(normalized):
            if _MED_TABLE_HEADER in text.replace(" ", ""):
                med_table_start = i
                break

        # 기본 처방 필드 파싱 (약품 테이블 이전까지만)
        parse_limit = med_table_start if med_table_start is not None else len(normalized)
        for i in range(parse_limit):
            clean = normalized[i].replace(" ", "")
            for keyword, field in field_keywords.items():
                if keyword in clean and result[field] is None:
                    for j in range(i + 1, min(i + 3, parse_limit)):
                        candidate = normalized[j].strip()
                        if not any(kw in candidate.replace(" ", "") for kw in label_set):
                            result[field] = candidate
                            break

        # 약품 테이블 파싱: 헤더 5개 건너뛰고 5열씩 묶어 약품 생성
        if med_table_start is not None:
            med_data = normalized[med_table_start + _NUM_MED_COLS:]
            for row_start in range(0, len(med_data), _NUM_MED_COLS):
                row = med_data[row_start: row_start + _NUM_MED_COLS]
                if not row:
                    break
                result["medications"].append(
                    {
                        "name": row[0] if len(row) > 0 else None,
                        "dosage": row[1] if len(row) > 1 else None,
                        "frequency": row[2] if len(row) > 2 else None,
                        "duration": row[3] if len(row) > 3 else None,
                        "instructions": row[4] if len(row) > 4 else None,
                    }
                )

        return result


def get_ocr_service() -> OcrServiceBase:
    if config.NAVER_OCR_SECRET and config.NAVER_OCR_URL:
        return NaverOcrService(config.NAVER_OCR_SECRET, config.NAVER_OCR_URL)
    return DummyOcrService()
