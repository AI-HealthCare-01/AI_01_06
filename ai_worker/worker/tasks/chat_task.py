import json
import logging

import redis.asyncio as aioredis

from app.core.redis import CHAT_STREAM_PREFIX
from app.models.chat import ChatMessage, ChatThread
from app.services.chat_service import build_context, get_chat_service
from worker import config
from worker.tools.weather_tool import is_weather_query, try_weather_response

logger = logging.getLogger(__name__)


def _extract_user_query(context: list[dict]) -> str:
    """컨텍스트에서 가장 마지막 user 메시지를 추출한다."""
    for msg in reversed(context):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


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

    try:
        # ── Weather tool: 날씨 질문 + 도시명 있을 때만 분기 ──
        user_query = _extract_user_query(context)
        weather_api_key = getattr(config, "WEATHER_API_KEY", "")
        weather_response = await try_weather_response(user_query, weather_api_key)

        if weather_response is not None:
            # 날씨 응답을 기존과 동일한 발행 형식으로 전달
            await on_progress(weather_response)
            assistant_msg.content = weather_response
            assistant_msg.status = "completed"
            await assistant_msg.save()
            await thread.save()
            await redis_client.publish(channel, json.dumps({"t": "done"}))
        elif weather_api_key and is_weather_query(user_query):
            # 날씨 질문이지만 도시명 없음 → 지역 입력 유도
            guide = '어느 지역의 날씨를 확인할까요?\n예: "서울 날씨 알려줘", "부산 기온 알려줘"'
            await on_progress(guide)
            assistant_msg.content = guide
            assistant_msg.status = "completed"
            await assistant_msg.save()
            await thread.save()
            await redis_client.publish(channel, json.dumps({"t": "done"}))
        else:
            # ── 기존 LLM 흐름 (변경 없음) ──
            chat_service = get_chat_service()
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
        await redis_client.publish(channel, json.dumps({"t": "error", "d": "응답 생성 중 오류가 발생했습니다."}))
    finally:
        await redis_client.aclose()
