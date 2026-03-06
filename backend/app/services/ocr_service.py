import abc


class OcrServiceBase(abc.ABC):
    @abc.abstractmethod
    async def extract(self, image_path: str) -> dict:
        ...


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
    """Naver Clova OCR integration (placeholder for real implementation)."""

    def __init__(self, secret: str, url: str) -> None:
        self.secret = secret
        self.url = url

    async def extract(self, image_path: str) -> dict:
        raise NotImplementedError("Naver OCR integration not yet implemented")


def get_ocr_service() -> OcrServiceBase:
    return DummyOcrService()
