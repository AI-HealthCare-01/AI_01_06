import abc
import json
import os

from openai import AsyncOpenAI

MEDICAL_DISCLAIMER = (
    "본 복약 가이드는 AI가 생성한 참고용 정보이며, 의학적 진단이나 처방을 대체하지 않습니다. "
    "정확한 진단과 처방은 반드시 의료 전문가와 상담하세요. "
    "약물 복용 중 이상 증상이 나타나면 즉시 의사와 상담하시기 바랍니다."
)

SYSTEM_PROMPT = "당신은 전문 약사입니다. 처방된 약물에 대한 복약 가이드를 JSON 형식으로 작성합니다."

RESPONSE_FORMAT_GUIDE = """
다음 JSON 형식으로만 응답해주세요:
{
  "medication_guides": [
    {
      "name": "약물명",
      "dosage": "용량",
      "frequency": "복용 횟수",
      "duration": "복용 기간",
      "instructions": "복용 지시",
      "effect": "효능 및 적응증",
      "precautions": "주의사항"
    }
  ],
  "warnings": {
    "drug_interactions": "약물 상호작용 주의사항",
    "side_effects": "주요 부작용",
    "alcohol": "음주 관련 주의사항"
  },
  "lifestyle": {
    "diet": ["식이 권장사항"],
    "exercise": ["운동 권장사항"]
  }
}
"""


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
    """OpenAI API를 사용한 복약 가이드 생성 서비스."""

    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key)

    def _build_prompt(self, medications: list[dict], user_info: dict) -> str:
        med_lines = "\n".join(
            f"- {m['name']} / 용량: {m.get('dosage', '-')} / 복용법: {m.get('frequency', '-')} "
            f"/ 기간: {m.get('duration', '-')} / 지시: {m.get('instructions', '-')}"
            for m in medications
        )
        return (
            f"환자 정보:\n"
            f"- 이름: {user_info.get('name', '알 수 없음')}\n"
            f"- 키/몸무게: {user_info.get('height', '-')}cm / {user_info.get('weight', '-')}kg\n"
            f"- 알레르기: {user_info.get('allergies') or '없음'}\n"
            f"- 기저질환: {user_info.get('conditions') or '없음'}\n\n"
            f"처방 약물:\n{med_lines}\n\n"
            f"{RESPONSE_FORMAT_GUIDE}"
        )

    async def generate(self, medications: list[dict], user_info: dict) -> dict:
        prompt = self._build_prompt(medications, user_info)
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = json.loads(response.choices[0].message.content)
        content["disclaimer"] = MEDICAL_DISCLAIMER
        return content


def get_guide_service() -> GuideServiceBase:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAIGuideService(api_key=api_key, model=model)
    return DummyGuideService()
