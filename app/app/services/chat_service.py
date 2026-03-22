import abc
import logging
from collections.abc import AsyncIterator, Awaitable, Callable

from openai import AsyncOpenAI

from app import config
from app.models.chat import ChatMessage, ChatThread
from app.models.patient_profile import PatientProfile
from app.models.prescription import Medication, Prescription
from app.services.retrieval_service import format_retrieved_docs, get_retrieval_service

logger = logging.getLogger(__name__)

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
    async def stream_reply(self, messages: list[dict]) -> AsyncIterator[str]: ...

    @abc.abstractmethod
    async def generate_reply(
        self,
        messages: list[dict],
        on_progress: Callable[[str], Awaitable[None]] | None = None,
        tools: list[dict] | None = None,
        tool_executor: Callable[[str, str], Awaitable[str]] | None = None,
    ) -> str: ...


class DummyChatService(ChatServiceBase):
    """테스트용 더미 채팅 서비스. 고정된 응답을 chunk로 반환."""

    async def stream_reply(self, messages: list[dict]) -> AsyncIterator[str]:
        response = "안녕하세요! 복약 관련 질문에 답변드리겠습니다. 궁금하신 점을 말씀해 주세요."
        for char in response:
            yield char

    async def generate_reply(
        self,
        messages: list[dict],
        on_progress: Callable[[str], Awaitable[None]] | None = None,
        tools: list[dict] | None = None,
        tool_executor: Callable[[str, str], Awaitable[str]] | None = None,
    ) -> str:
        response = "안녕하세요! 복약 관련 질문에 답변드리겠습니다. 궁금하신 점을 말씀해 주세요."
        if on_progress:
            await on_progress(response)
        return response


class OpenAIChatService(ChatServiceBase):
    """OpenAI 기반 채팅 서비스."""

    def __init__(self, api_key: str, model: str) -> None:
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

    @staticmethod
    def _accumulate_tool_call(tool_calls_data: list[dict], tc) -> None:
        """스트리밍 청크에서 tool_call 데이터를 누적한다."""
        while len(tool_calls_data) <= tc.index:
            tool_calls_data.append({"id": "", "name": "", "arguments": ""})
        entry = tool_calls_data[tc.index]
        if tc.id:
            entry["id"] = tc.id
        if tc.function and tc.function.name:
            entry["name"] = tc.function.name
        if tc.function and tc.function.arguments:
            entry["arguments"] += tc.function.arguments

    async def generate_reply(
        self,
        messages: list[dict],
        on_progress: Callable[[str], Awaitable[None]] | None = None,
        tools: list[dict] | None = None,
        tool_executor: Callable[[str, str], Awaitable[str]] | None = None,
    ) -> str:
        create_kwargs: dict = {"model": self.model, "messages": messages, "stream": True}
        if tools:
            create_kwargs["tools"] = tools
            create_kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**create_kwargs)
        accumulated = ""
        tool_calls_data: list[dict] = []

        try:
            async for chunk in response:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue

                if choice.delta.content:
                    accumulated += choice.delta.content
                    if on_progress:
                        await on_progress(accumulated)

                if choice.delta.tool_calls:
                    for tc in choice.delta.tool_calls:
                        self._accumulate_tool_call(tool_calls_data, tc)
        finally:
            await response.close()

        if tool_calls_data and tool_executor:
            await self._execute_tool_calls(messages, accumulated, tool_calls_data, tool_executor)
            return await self.generate_reply(messages, on_progress=on_progress)

        if on_progress:
            await on_progress(accumulated)
        return accumulated

    @staticmethod
    async def _execute_tool_calls(
        messages: list[dict],
        accumulated: str,
        tool_calls_data: list[dict],
        tool_executor: Callable[[str, str], Awaitable[str]],
    ) -> None:
        """tool_call 결과를 messages에 추가한다."""
        assistant_msg = {
            "role": "assistant",
            "content": accumulated or None,
            "tool_calls": [
                {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                for tc in tool_calls_data
            ],
        }
        messages.append(assistant_msg)
        for tc in tool_calls_data:
            result = await tool_executor(tc["name"], tc["arguments"])
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})


def get_chat_service() -> ChatServiceBase:
    if config.OPENAI_API_KEY:
        return OpenAIChatService(api_key=config.OPENAI_API_KEY, model=config.OPENAI_MODEL)
    return DummyChatService()


RAG_INSTRUCTION = (
    "\n\n[근거 기반 답변 원칙]\n"
    "- [참고 자료]가 제공된 경우 해당 내용을 근거로 답변하세요.\n"
    "- 참고 자료에 없는 내용은 솔직히 '해당 정보가 없다'고 안내하세요.\n"
    "- 약품명, 용량, 횟수 등 수치는 자료에 있는 그대로만 사용하세요."
)


async def build_retrieved_context(thread: ChatThread, medications: list, user_query: str) -> list[dict]:
    """처방전 약품 기반 RAG 검색 결과를 system message로 반환한다.

    retrieval 실패 시 빈 리스트를 반환하여 기존 채팅 흐름을 유지한다.
    """
    try:
        drug_names = [m.name for m in medications]
        logger.info("[RAG] drug_names=%s, query=%s", drug_names, user_query[:50])
        if not drug_names:
            return []

        retrieval_service = get_retrieval_service()
        docs = await retrieval_service.retrieve(drug_names, user_query)
        logger.info("[RAG] retrieved %d docs", len(docs))
        if not docs:
            return []

        ref_text = format_retrieved_docs(docs)
        logger.info("[RAG] context length=%d chars", len(ref_text))
        if not ref_text:
            return []

        return [
            {
                "role": "system",
                "content": (
                    "[참고 자료]\n"
                    "아래는 처방된 약품의 공식 정보입니다. "
                    "답변 시 이 정보를 근거로 활용하세요.\n\n" + ref_text
                ),
            }
        ]
    except Exception:
        logger.exception("[RAG] retrieval failed")
        return []


async def build_context(thread: ChatThread) -> list[dict]:  # noqa: C901
    """LLM에 전달할 메시지 컨텍스트를 구성합니다."""
    system_content = SYSTEM_PROMPT
    if config.RAG_ENABLED:
        system_content += RAG_INSTRUCTION
    messages: list[dict] = [{"role": "system", "content": system_content}]

    # 처방전 요약
    medications = []
    if thread.prescription_id:
        prescription = await Prescription.get(id=thread.prescription_id)
        medications = await Medication.filter(prescription=prescription)

        summary_parts = []
        if prescription.hospital_name:
            summary_parts.append(f"병원: {prescription.hospital_name}")
        if prescription.diagnosis:
            summary_parts.append(f"진단: {prescription.diagnosis}")
        if medications:
            med_names = ", ".join(m.name for m in medications)
            summary_parts.append(f"처방 약물: {med_names}")

        profile = await PatientProfile.get_or_none(user_id=thread.user_id)
        if profile and profile.allergy_details:
            summary_parts.append(f"알러지: {profile.allergy_details}")
        if profile and profile.disease_details:
            summary_parts.append(f"기저질환: {profile.disease_details}")

        if summary_parts:
            messages.append(
                {
                    "role": "system",
                    "content": "[처방전 요약]\n" + "\n".join(summary_parts),
                }
            )

    # 최근 completed 메시지 (현재 사용자 메시지 포함)
    recent = (
        await ChatMessage.filter(thread=thread, status="completed")
        .order_by("-created_at")
        .limit(config.CHAT_CONTEXT_MESSAGE_COUNT)
    )
    recent_list = list(reversed(recent))

    # RAG: 처방전이 연결된 경우에만 검색 수행
    med_count = len(medications)
    recent_count = len(recent_list)
    logger.info("[RAG] enabled=%s, medications=%d, recent=%d", config.RAG_ENABLED, med_count, recent_count)

    if config.RAG_ENABLED and medications and recent_list:
        # 가장 최근 user 메시지에서 질문 추출
        user_query = ""
        for m in reversed(recent_list):
            if m.role == "user":
                user_query = m.content
                break

        if user_query:
            retrieved = await build_retrieved_context(thread, medications, user_query)
            messages.extend(retrieved)

    for m in recent_list:
        messages.append({"role": m.role, "content": m.content})

    return messages
