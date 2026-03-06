from unittest.mock import AsyncMock, patch

import pytest

from app.core.redis import close_redis_pool, enqueue


@pytest.fixture(autouse=True)
async def _reset_pool():
    """Reset global pool before/after each test."""
    from app.core import redis
    redis._pool = None
    yield
    redis._pool = None


async def test_enqueue_returns_job_id():
    mock_job = AsyncMock()
    mock_job.job_id = "test-job-123"

    mock_pool = AsyncMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

    with patch("app.core.redis.create_pool", return_value=mock_pool):
        job_id = await enqueue("ocr_task", 1, 2)

    assert job_id == "test-job-123"
    mock_pool.enqueue_job.assert_called_once_with("ocr_task", 1, 2)


async def test_enqueue_returns_none_when_duplicate():
    mock_pool = AsyncMock()
    mock_pool.enqueue_job = AsyncMock(return_value=None)

    with patch("app.core.redis.create_pool", return_value=mock_pool):
        job_id = await enqueue("ocr_task", 1)

    assert job_id is None


async def test_close_redis_pool():
    mock_pool = AsyncMock()

    with patch("app.core.redis.create_pool", return_value=mock_pool):
        await enqueue("dummy")  # initializes pool
        await close_redis_pool()

    mock_pool.aclose.assert_called_once()
