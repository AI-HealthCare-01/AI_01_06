import pytest
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

from app.main import app

TEST_DB_URL = "sqlite://:memory:"


@pytest.fixture(autouse=True)
async def setup_db():
    await Tortoise.init(
        db_url=TEST_DB_URL,
        modules={"models": ["app.models.user", "app.models.prescription", "app.models.guide"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client: AsyncClient):
    """Returns a client with a logged-in patient user and the user data."""
    signup_data = {
        "email": "test@example.com",
        "password": "Test1234!",
        "nickname": "테스트유저",
        "name": "홍길동",
        "role": "patient",
    }
    await client.post("/api/auth/signup", json=signup_data)
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Test1234!"},
    )
    token = login_resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
