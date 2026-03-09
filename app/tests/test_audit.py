import pytest
from httpx import AsyncClient

from app.models.audit import AuditLog

_SIGNUP = {
    "email": "audit@test.com",
    "password": "Pass1234!",
    "nickname": "감사닉",
    "name": "감사",
    "terms_of_service": True,
    "privacy_policy": True,
}


@pytest.mark.asyncio
async def test_login_creates_audit_log(client: AsyncClient):
    await client.post("/api/auth/signup", json=_SIGNUP)
    await client.post("/api/auth/login", json={"email": _SIGNUP["email"], "password": _SIGNUP["password"]})

    logs = await AuditLog.filter(action_type="LOGIN", outcome="SUCCESS")
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_failed_login_creates_failure_audit_log(client: AsyncClient):
    await client.post("/api/auth/signup", json=_SIGNUP)
    await client.post("/api/auth/login", json={"email": _SIGNUP["email"], "password": "WrongPass1!"})

    logs = await AuditLog.filter(action_type="LOGIN", outcome="FAILURE")
    assert len(logs) == 1
