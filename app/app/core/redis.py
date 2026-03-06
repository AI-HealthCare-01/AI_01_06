from arq.connections import ArqRedis, RedisSettings, create_pool

from app import config

_pool: ArqRedis | None = None


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


async def enqueue(task_name: str, *args, **kwargs) -> str | None:
    """Enqueue a task to the arq worker. Returns the job id."""
    pool = await get_redis_pool()
    job = await pool.enqueue_job(task_name, *args, **kwargs)
    return job.job_id if job else None
