import abc
import json
import os

from openai import AsyncOpenAI

MEDICAL_DISCLAIMER = (
    "본 복약 가이드는 AI가 생성한 참고용 정보이며, 의학적 진단이나 처방을 대체하지 않습니다. "
    "정확한 진단과 처방은 반드시 의료 전문가와 상담하세요. "
    "약물 복용 중 이상 증상이 나타나면 즉시 의사와 상담하시기 바랍니다."
)

SYSTEM_PROMPT = (
    "당신은 대한민국 면허 약사입니다. 처방된 약물에 대한 복약 가이드를 JSON 형식으로 작성합니다.\n"
    "작성 기준:\n"
    "- 약물 상호작용: 처방된 약물 간 실제 상호작용만 명시. 없으면 '해당 약물 간 주요 상호작용 없음'으로 작성.\n"
    "- 부작용: 해당 약물의 대표적인 부작용을 구체적 증상으로 명시. 예: '구역, 두통, 어지러움'\n"
    "- 음주: 각 약물의 음주 금기 여부를 명확히 명시. 금기 시 '복용 중 음주 금지'로 작성.\n"
    "- instructions에 복용 횟수, 시간대, 방법을 한 문장으로 통합 작성할 것. "
    "예: '1일 3회 아침·점심·저녁 식후 30분 복용'\n"
    "- 환자 프로필(생년월일, 성별, 키/몸무게, 알레르기, 기저질환)이 제공된 경우, 해당 정보를 반영하여 개인화된 복약 지도를 작성할 것.\n"
    "- 모든 항목은 한국어로, 간결하고 명확하게 작성할 것."
)

RESPONSE_FORMAT_GUIDE = """
다음 JSON 형식으로만 응답해주세요:
{
  "medication_guides": [
    {
      "name": "약물명",
      "dosage": "1회 복용량",
      "duration": "복용 기간",
      "instructions": "복용법 (횟수+시간대+방법을 한 문장으로. 예: '1일 3회 아침·점심·저녁 식후 30분 복용')",
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
            freq = med.get("frequency", "")
            instr = med.get("instructions", "")
            combined = instr if instr else freq
            medication_guides.append(
                {
                    "name": med.get("name", ""),
                    "dosage": med.get("dosage", ""),
                    "duration": med.get("duration", ""),
                    "instructions": combined,
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

        patient_lines = []
        birth_date = user_info.get("birth_date")
        gender = user_info.get("gender")
        if birth_date or gender:
            patient_lines.append(f"- 생년월일/성별: {birth_date or '-'} / {gender or '-'}")

        if user_info.get("has_profile"):
            height = user_info.get("height")
            weight = user_info.get("weight")
            patient_lines.append(
                f"- 키/몸무게: {height if height is not None else '-'}cm / {weight if weight is not None else '-'}kg"
            )
            patient_lines.append(f"- 알레르기: {user_info.get('allergies') or '없음'}")
            patient_lines.append(f"- 기저질환: {user_info.get('conditions') or '없음'}")

        patient_section = "\n".join(patient_lines) if patient_lines else "- 환자 정보 없음"

        return f"환자 정보:\n{patient_section}\n\n처방 약물:\n{med_lines}\n\n{RESPONSE_FORMAT_GUIDE}"

    async def generate(self, medications: list[dict], user_info: dict) -> dict:
        prompt = self._build_prompt(medications, user_info)
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
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
