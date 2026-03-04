import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from ai_worker.chat.service import ChatService
from ai_worker.chat.session import RedisSessionManager
from ai_worker.core.config import Config
from ai_worker.guide.service import GuideService
from ai_worker.llm.client import get_openai_client
from ai_worker.schemas.guide import GuideRequest, GuideResponse

config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.openai = get_openai_client(api_key=config.OPENAI_API_KEY)
    app.state.redis = await aioredis.from_url(config.REDIS_URL)
    yield
    await app.state.openai.close()
    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/llm/ping")
async def llm_ping(request: Request):
    client = request.app.state.openai
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not set")

    try:
        await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": "say ping"}],
            max_tokens=5,
        )
        return {"status": "ok", "reply": f"pong from {config.OPENAI_MODEL}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/guide", response_model=GuideResponse)
async def create_guide(req: GuideRequest, request: Request):
    service = GuideService()
    return await service.generate(req, request.app.state.openai)


@app.get("/chat/{thread_id}/stream")
async def chat_stream(thread_id: str, request: Request, message: str):
    client = request.app.state.openai
    redis_client = request.app.state.redis

    session_manager = RedisSessionManager(redis_client)
    await session_manager.append_message(thread_id, "user", message)

    history = await session_manager.get_history(thread_id)
    messages = [{"role": msg.role, "content": msg.content} for msg in history]

    service = ChatService()

    async def chat_generator() -> AsyncIterator[str]:
        chunks: list[str] = []
        async for chunk in service.stream_response(client, messages):
            try:
                data_str = chunk[6:].strip()  # remove "data: "
                if data_str:
                    data = json.loads(data_str)
                    delta = data.get("delta", "")
                    if delta:
                        chunks.append(delta)
            except json.JSONDecodeError:
                pass
            yield chunk

        full_response = "".join(chunks)
        if full_response:
            await session_manager.append_message(thread_id, "assistant", full_response)

    return StreamingResponse(chat_generator(), media_type="text/event-stream")
