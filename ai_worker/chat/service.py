import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from ai_worker.llm.prompts.chat import CHAT_SYSTEM_PROMPT


class ChatService:
    async def stream_response(
        self,
        client: AsyncOpenAI,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        full_messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + messages

        stream = await client.chat.completions.create(
            model="gpt-4o-mini", messages=full_messages, temperature=0.5, stream=True
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'delta': content}, ensure_ascii=False)}\n\n"
