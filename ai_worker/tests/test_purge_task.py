from datetime import UTC, datetime, timedelta

import pytest

from app.models.auth_provider import AuthProvider
from app.models.patient_profile import PatientProfile
from app.models.user import User
from worker.tasks.purge_task import purge_deleted_users


@pytest.mark.asyncio
async def test_purge_deletes_expired_users():
    """30일 경과 소프트 삭제 계정 → 물리 삭제."""
    user = await User.create(
        email="expired@test.com",
        password_hash="hashed",
        nickname="만료유저",
        name="만료",
        role="PATIENT",
        deleted_at=datetime.now(UTC) - timedelta(days=31),
    )
    await purge_deleted_users({})
    assert await User.get_or_none(id=user.id) is None


@pytest.mark.asyncio
async def test_purge_preserves_recent_deletes():
    """30일 미경과 소프트 삭제 계정 → 보존."""
    user = await User.create(
        email="recent@test.com",
        password_hash="hashed",
        nickname="최근유저",
        name="최근",
        role="PATIENT",
        deleted_at=datetime.now(UTC) - timedelta(days=10),
    )
    await purge_deleted_users({})
    assert await User.get_or_none(id=user.id) is not None


@pytest.mark.asyncio
async def test_purge_cascades_related_data():
    """물리 삭제 시 AuthProvider, PatientProfile 등 연관 데이터도 삭제."""
    user = await User.create(
        email="cascade@test.com",
        password_hash="hashed",
        nickname="캐스케이드유저",
        name="캐스케이드",
        role="PATIENT",
        deleted_at=datetime.now(UTC) - timedelta(days=31),
    )
    await AuthProvider.create(user=user, provider="LOCAL", provider_user_id="cascade@test.com")
    await PatientProfile.create(user=user)

    await purge_deleted_users({})

    assert await User.get_or_none(id=user.id) is None
    assert await AuthProvider.filter(user_id=user.id).count() == 0
    assert await PatientProfile.filter(user_id=user.id).count() == 0
