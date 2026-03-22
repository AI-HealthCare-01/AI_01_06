import json
import logging

import redis.asyncio as aioredis

from app.core.redis import CHAT_STREAM_PREFIX
from app.models.chat import ChatMessage, ChatThread
from app.services.chat_service import build_context, get_chat_service
from worker import config
from worker.tools.weather_tool import (
    _CITY_MAP,
    WEATHER_TOOL_SCHEMA,
    _find_korean_city_name,
    fetch_weather,
    format_weather_response,
)

logger = logging.getLogger(__name__)


async def _execute_tool(name: str, arguments: str) -> str:
    """tool_call을 실행하고 결과 문자열을 반환한다."""
    args = json.loads(arguments)
    if name == "get_weather":
        weather_api_key = getattr(config, "WEATHER_API_KEY", "")
        if not weather_api_key:
            return "날씨 API 키가 설정되지 않았습니다."
        raw_city = args.get("city", "")
        # 한국어 도시명 → OpenWeatherMap 영어 도시명 변환
        api_city = _CITY_MAP.get(raw_city, raw_city)
        city_kr = _find_korean_city_name(api_city) or raw_city
        try:
            data = await fetch_weather(api_city, weather_api_key)
            return format_weather_response(data, city_kr)
        except Exception:
            logger.exception("[Weather] fetch failed for city=%s (api_city=%s)", raw_city, api_city)
            return f"'{raw_city}' 날씨 정보를 가져올 수 없습니다."
    return f"알 수 없는 도구: {name}"


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

    _last_len = 0

    async def on_progress(accumulated: str) -> None:
        nonlocal _last_len
        if len(accumulated) < _last_len:
            _last_len = 0
        delta = accumulated[_last_len:]
        if delta:
            await redis_client.publish(channel, json.dumps({"t": "c", "d": delta}))
            _last_len = len(accumulated)

    try:
        chat_service = get_chat_service()

        tools: list[dict] = []
        if getattr(config, "WEATHER_API_KEY", ""):
            tools.append(WEATHER_TOOL_SCHEMA)

        content = await chat_service.generate_reply(
            context,
            on_progress=on_progress,
            tools=tools or None,
            tool_executor=_execute_tool if tools else None,
        )
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
