import os

import pytest
from tortoise import Tortoise

# Get database URL directly from environment - usually injected by Docker Compose
# Fallback to local default just in case, but prefer the env var
DATABASE_URL = os.getenv("DATABASE_URL", "mysql://root:root@mysql:3306/sullivan")

# 기본적으로 skip. Docker가 실행 중일 때만 DB_INTEGRATION_TEST=1 로 활성화.
# 실행 방법: DB_INTEGRATION_TEST=1 uv run pytest tests/integration/
pytestmark = pytest.mark.skipif(
    os.getenv("DB_INTEGRATION_TEST") != "1",
    reason="Docker MySQL 필요. DB_INTEGRATION_TEST=1 환경변수 설정 후 실행하세요.",
)


@pytest.mark.asyncio
async def test_mysql_connection():
    """
    TDD Red -> Green: Ensure our application can physically connect to the MySQL database
    defined in docker-compose.yaml across the container network.
    Because we only want to test connection state and not re-test ORM behaviors,
    we perform a raw query 'SELECT 1'.
    """
    try:
        # Initialize Tortoise solely with our test URL for pinging
        await Tortoise.init(
            db_url=DATABASE_URL,
            modules={"models": ["app.models.user"]},  # Tortoise requires at least one model path
        )

        # Get raw connection
        conn = Tortoise.get_connection("default")

        # Execute basic ping query
        result = await conn.execute_query("SELECT 1")

        # Must return some data
        assert result is not None, "Failed to get a response from database"

    finally:
        # Always clean up the connection
        await Tortoise.close_connections()
