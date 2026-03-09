import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.guide_service import OpenAIGuideService

SAMPLE_MEDICATIONS = [
    {
        "name": "아스피린",
        "dosage": "100mg",
        "frequency": "1일 1회",
        "duration": "30일",
        "instructions": "식후 복용",
    }
]

SAMPLE_USER_INFO = {
    "name": "홍길동",
    "height": 175.0,
    "weight": 70.0,
    "allergies": None,
    "conditions": None,
}

SAMPLE_LLM_RESPONSE = {
    "medication_guides": [
        {
            "name": "아스피린",
            "dosage": "100mg",
            "frequency": "1일 1회",
            "duration": "30일",
            "instructions": "식후 복용",
            "effect": "혈전 예방",
            "precautions": "공복 복용 금지",
        }
    ],
    "warnings": {
        "drug_interactions": "다른 혈액희석제와 병용 주의",
        "side_effects": "위장 출혈 가능",
        "alcohol": "음주 자제",
    },
    "lifestyle": {
        "diet": ["저염식 권장"],
        "exercise": ["가벼운 유산소 운동 권장"],
    },
}


def _make_mock_client(response_dict: dict) -> AsyncMock:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(response_dict)
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


async def test_openai_guide_service_returns_medication_guides_and_disclaimer():
    """OpenAIGuideService가 LLM 응답을 파싱하고 disclaimer를 포함한 결과를 반환한다."""
    mock_client = _make_mock_client(SAMPLE_LLM_RESPONSE)

    with patch("app.services.guide_service.AsyncOpenAI", return_value=mock_client):
        service = OpenAIGuideService(api_key="test-key", model="gpt-4o-mini")
        result = await service.generate(SAMPLE_MEDICATIONS, SAMPLE_USER_INFO)

    assert "medication_guides" in result
    assert "disclaimer" in result
    assert len(result["medication_guides"]) == 1


async def test_openai_guide_service_sends_medication_name_in_prompt():
    """OpenAIGuideService가 약물 이름을 포함한 프롬프트로 OpenAI API를 호출한다."""
    mock_client = _make_mock_client(SAMPLE_LLM_RESPONSE)

    with patch("app.services.guide_service.AsyncOpenAI", return_value=mock_client):
        service = OpenAIGuideService(api_key="test-key", model="gpt-4o-mini")
        await service.generate(SAMPLE_MEDICATIONS, SAMPLE_USER_INFO)

    create_call = mock_client.chat.completions.create.call_args
    messages = create_call.kwargs["messages"]
    user_prompt = next(m["content"] for m in messages if m["role"] == "user")
    assert "아스피린" in user_prompt
