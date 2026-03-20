import json
import logging

import redis.asyncio as aioredis

from app.models.chat import ChatMessage, ChatThread
from app.services.chat_service import build_context, get_chat_service
from worker import config

logger = logging.getLogger(__name__)

CHAT_STREAM_PREFIX = "chat:stream:"


async def chat_task(ctx: dict, message_id: int) -> None:
    """ARQ 태스크: LLM 응답을 생성하고 Redis Pub/Sub로 실시간 발행, DB에 저장한다."""
    assistant_msg = await ChatMessage.get_or_none(id=message_id)
    if not assistant_msg:
        logger.error("ChatMessage %d not found", message_id)
        return

    thread = await ChatThread.get(id=assistant_msg.thread_id)
    context = await build_context(thread)

    redis_client = aioredis.from_url(config.REDIS_URL, decode_responses=True)
    channel = f"{CHAT_STREAM_PREFIX}{message_id}"

    async def on_progress(accumulated: str) -> None:
        await redis_client.publish(channel, json.dumps({"t": "c", "d": accumulated}))

    chat_service = get_chat_service()
    try:
        content = await chat_service.generate_reply(context, on_progress=on_progress)
        assistant_msg.content = content
        assistant_msg.status = "completed"
        await assistant_msg.save()
        await thread.save()
        await redis_client.publish(channel, json.dumps({"t": "done"}))
    except Exception:
        logger.exception("chat_task failed for message %d", message_id)
        assistant_msg.status = "failed"
        await assistant_msg.save()
        await thread.save()
        await redis_client.publish(
            channel, json.dumps({"t": "error", "d": "응답 생성 중 오류가 발생했습니다."})
        )
    finally:
        await redis_client.aclose()
