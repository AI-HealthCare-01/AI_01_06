import redis.asyncio as aioredis
from arq.connections import ArqRedis, RedisSettings, create_pool

from app import config

_pool: ArqRedis | None = None
_state_redis: aioredis.Redis | None = None


async def get_redis_pool() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(config.REDIS_URL))
    return _pool


async def close_redis_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def get_state_redis() -> aioredis.Redis:
    """ARQ 큐와 독립된 일반 key-value Redis 클라이언트 (OAuth state 등 사용)."""
    global _state_redis
    if _state_redis is None:
        _state_redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)
    return _state_redis


async def close_state_redis() -> None:
    global _state_redis
    if _state_redis is not None:
        await _state_redis.aclose()
        _state_redis = None


async def enqueue(task_name: str, *args, **kwargs) -> str | None:
    """Enqueue a task to the arq worker. Returns the job id."""
    pool = await get_redis_pool()
    job = await pool.enqueue_job(task_name, *args, **kwargs)
    return job.job_id if job else None


CHAT_STREAM_PREFIX = "chat:stream:"


async def subscribe_chat_stream(message_id: int) -> tuple[aioredis.client.PubSub, aioredis.Redis]:
    """채팅 메시지 스트림 Pub/Sub 구독을 시작한다.

    Returns:
        (pubsub, redis_client) 튜플. 사용 후 반드시 unsubscribe + aclose 호출 필요.
    """
    redis_client = aioredis.from_url(config.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"{CHAT_STREAM_PREFIX}{message_id}")
    return pubsub, redis_client
