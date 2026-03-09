import pytest
from httpx import AsyncClient

from app.models.auth_provider import AuthProvider
from app.models.user import User


@pytest.mark.asyncio
async def test_signup_creates_local_auth_provider(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={
            "email": "new@test.com",
            "password": "Pass1234!",
            "nickname": "신규유저",
            "name": "테스트",
        },
    )
    assert resp.json()["success"] is True
    user = await User.filter(email="new@test.com").first()
    provider = await AuthProvider.filter(user=user).first()
    assert provider is not None
    assert provider.provider == "LOCAL"
    assert provider.provider_user_id == "new@test.com"
