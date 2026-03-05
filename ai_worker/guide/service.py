from openai import AsyncOpenAI

from ai_worker.llm.prompts.guide import GUIDE_SYSTEM_PROMPT
from ai_worker.schemas.guide import GuideRequest, GuideResponse


class GuideService:
    async def generate(self, request: GuideRequest, client: AsyncOpenAI) -> GuideResponse:
        messages = [
            {"role": "system", "content": GUIDE_SYSTEM_PROMPT},
            {"role": "user", "content": f"처방전: {request.ocr_result}\n\n사용자 프로필: {request.user_profile}"},
        ]

        response = await client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.3)

        content = response.choices[0].message.content or ""
        disclaimer = "이 정보는 AI에 의해 생성되었으며, 전문적인 의학적 조언을 대신할 수 없습니다. 의문사항은 반드시 전문의와 상담하십시오."

        return GuideResponse(guide_text=content, disclaimer=disclaimer)
