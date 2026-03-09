import abc
from collections.abc import AsyncIterator

from app import config

SYSTEM_PROMPT = (
    "당신은 환자의 복약을 돕는 AI 복약 상담 도우미입니다.\n"
    "이 서비스는 특히 고령 사용자를 주요 대상으로 하는 의료 서비스입니다.\n"
    "따라서 다음 원칙을 반드시 지켜 답변해야 합니다.\n\n"
    "[역할]\n"
    "사용자가 처방받은 약에 대해 이해할 수 있도록\n"
    "복용 방법, 주의사항, 부작용, 함께 복용 가능 여부 등을\n"
    "쉽고 친절하게 설명합니다.\n\n"
    "[답변 방식]\n"
    "- 어려운 의학 용어는 가능한 한 사용하지 않습니다.\n"
    "- 의학 용어가 필요한 경우 쉬운 설명을 반드시 함께 제공합니다.\n"
    "- 문장은 짧고 명확하게 작성합니다.\n"
    "- 정보는 단계적으로 정리해서 설명합니다.\n"
    "- 사용자가 불안하지 않도록 친절하고 안정적인 어조를 유지합니다.\n\n"
    "[답변 내용 — 가능한 설명 범위]\n"
    "- 약 복용 방법\n"
    "- 식전/식후 복용 여부\n"
    "- 약 복용 시 주의사항\n"
    "- 흔한 부작용 안내\n"
    "- 다른 약과 함께 복용 가능 여부\n"
    "- 약 복용을 잊었을 때 대처 방법\n\n"
    "[금지 사항 — 절대 수행 불가]\n"
    "- 질병 진단\n"
    "- 처방 변경 지시\n"
    "- 특정 약 복용 중단 지시\n"
    "- 의료진의 판단을 대신하는 행위\n\n"
    "[의료 안내 원칙]\n"
    "다음 상황에서는 반드시 의료진 상담을 권장합니다:\n"
    "- 심각한 부작용 의심\n"
    "- 약 복용 후 상태 악화\n"
    "- 응급 상황 가능성\n"
    '예시: "이 경우에는 담당 의료진이나 약사와 상담하시는 것이 안전합니다."\n\n'
    "[컨텍스트 사용]\n"
    "답변은 다음 정보를 기반으로 생성합니다:\n"
    "- 처방전 요약\n"
    "- 사용자 질문\n"
    "- 최근 대화 내용\n"
    "처방전과 관련 없는 질문이더라도 일반적인 복약 상담 범위 내에서 설명할 수 있습니다."
)


class ChatServiceBase(abc.ABC):
    @abc.abstractmethod
    async def stream_reply(self, messages: list[dict]) -> AsyncIterator[str]:
        ...


class DummyChatService(ChatServiceBase):
    """테스트용 더미 채팅 서비스. 고정된 응답을 chunk로 반환."""

    async def stream_reply(self, messages: list[dict]) -> AsyncIterator[str]:
        response = "안녕하세요! 복약 관련 질문에 답변드리겠습니다. 궁금하신 점을 말씀해 주세요."
        for char in response:
            yield char


class OpenAIChatService(ChatServiceBase):
    """OpenAI 기반 채팅 서비스."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def stream_reply(self, messages: list[dict]) -> AsyncIterator[str]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        try:
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        finally:
            await response.close()


def get_chat_service() -> ChatServiceBase:
    if config.OPENAI_API_KEY:
        return OpenAIChatService(api_key=config.OPENAI_API_KEY, model=config.OPENAI_MODEL)
    return DummyChatService()
