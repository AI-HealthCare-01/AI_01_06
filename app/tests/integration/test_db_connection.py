import os
import pytest
from tortoise import Tortoise

# Get database URL directly from environment - usually injected by Docker Compose
# Fallback to local default just in case, but prefer the env var
DATABASE_URL = os.getenv("DATABASE_URL", "mysql://root:root@mysql:3306/sullivan")

# Make this test skip if NO_DB_INTEGRATION_TEST environment variable is set
# This helps in environments where docker is not running (e.g., standard CI without DB)
pytestmark = pytest.mark.skipif(
    os.getenv("NO_DB_INTEGRATION_TEST") == "1",
    reason="Database integration tests are disabled via NO_DB_INTEGRATION_TEST=1"
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
            modules={"models": ["app.models.user"]}  # Tortoise requires at least one model path
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
