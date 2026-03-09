import abc

MEDICAL_DISCLAIMER = (
    "본 복약 가이드는 AI가 생성한 참고용 정보이며, 의학적 진단이나 처방을 대체하지 않습니다. "
    "정확한 진단과 처방은 반드시 의료 전문가와 상담하세요. "
    "약물 복용 중 이상 증상이 나타나면 즉시 의사와 상담하시기 바랍니다."
)


class GuideServiceBase(abc.ABC):
    @abc.abstractmethod
    async def generate(self, medications: list[dict], user_info: dict) -> dict: ...


class DummyGuideService(GuideServiceBase):
    """Stub guide generator. Replace with OpenAI-based service for production."""

    async def generate(self, medications: list[dict], user_info: dict) -> dict:
        medication_guides = []
        for med in medications:
            medication_guides.append(
                {
                    "name": med.get("name", ""),
                    "dosage": med.get("dosage", ""),
                    "frequency": med.get("frequency", ""),
                    "duration": med.get("duration", ""),
                    "instructions": med.get("instructions", ""),
                    "effect": "증상 완화 및 관리",
                    "precautions": "공복 복용 시 위장 장애 가능",
                }
            )

        return {
            "medication_guides": medication_guides,
            "warnings": {
                "drug_interactions": "복약 정보에 있는 약물들간의 상호작용을 확인하세요.",
                "side_effects": "부작용 증상(심한 복통, 혈변, 호흡곤란) 등이 나타나면 즉시 의사와 상담하세요.",
                "alcohol": "복용 기간 동안 과도한 음주는 질병 유발 위험이 있습니다.",
            },
            "lifestyle": {
                "diet": ["탄수화물 섭취를 적절히 조절하세요", "염분 섭취를 줄이세요"],
                "exercise": ["하루 30분 이상 걷기 운동을 권장합니다"],
            },
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class OpenAIGuideService(GuideServiceBase):
    """OpenAI-based guide generation (placeholder for real implementation)."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def generate(self, medications: list[dict], user_info: dict) -> dict:
        raise NotImplementedError("OpenAI guide generation not yet implemented")


def get_guide_service() -> GuideServiceBase:
    return DummyGuideService()
