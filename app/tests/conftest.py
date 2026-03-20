import os
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

from app.core.rate_limit import limiter
from app.main import app
from app.models.chat import ChatMessage, ChatThread
from app.models.guide import Guide
from app.models.patient_profile import PatientProfile
from app.models.prescription import Medication, Prescription
from app.models.user import User
from app.services.chat_service import build_context, get_chat_service
from app.services.guide_service import get_guide_service
from app.services.icd_service import resolve_diagnosis
from app.services.ocr_service import get_ocr_service

TEST_DB_URL = "sqlite://:memory:"


async def _fake_enqueue(task_name: str, *args, **kwargs) -> str:
    """Simulate worker inline: run OCR/guide synchronously for tests."""
    if task_name == "ocr_task":
        prescription_id = args[0]
        filepath = args[1] if len(args) > 1 else None
        prescription = await Prescription.get(id=prescription_id)
        ocr_service = get_ocr_service()
        ocr_result = await ocr_service.extract(filepath or "")

        prescription.hospital_name = ocr_result.get("hospital_name")
        prescription.doctor_name = ocr_result.get("doctor_name")
        prescription.prescription_date = ocr_result.get("prescription_date")
        prescription.diagnosis = await resolve_diagnosis(ocr_result.get("diagnosis"))
        prescription.ocr_raw = ocr_result
        prescription.ocr_status = "ocr_completed"
        await prescription.save()

        for med_data in ocr_result.get("medications", []):
            await Medication.create(
                prescription=prescription,
                name=med_data["name"],
                dosage=med_data.get("dosage"),
                frequency=med_data.get("frequency"),
                duration=med_data.get("duration"),
                instructions=med_data.get("instructions"),
            )

        if filepath:
            try:
                os.remove(filepath)
            except OSError:
                pass
    elif task_name == "chat_task":
        message_id = args[0]
        assistant_msg = await ChatMessage.get(id=message_id)
        thread = await ChatThread.get(id=assistant_msg.thread_id)
        context = await build_context(thread)
        chat_service = get_chat_service()
        content = await chat_service.generate_reply(context)
        assistant_msg.content = content
        assistant_msg.status = "completed"
        await assistant_msg.save()
        await thread.save()
    elif task_name == "guide_task":
        guide_id = args[0]
        user_id = args[1]
        guide = await Guide.get(id=guide_id)
        prescription = await Prescription.get(id=guide.prescription_id)
        user = await User.get(id=user_id)

        medications = await Medication.filter(prescription=prescription)
        med_list = [
            {
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "duration": m.duration,
                "instructions": m.instructions,
            }
            for m in medications
        ]
        profile = await PatientProfile.get_or_none(user=user)
        user_info = {
            "birth_date": str(user.birth_date) if user.birth_date else None,
            "gender": user.gender,
            "has_profile": profile is not None,
            "height": float(profile.height_cm) if profile and profile.height_cm is not None else None,
            "weight": float(profile.weight_kg) if profile and profile.weight_kg is not None else None,
            "allergies": profile.allergy_details if profile else None,
            "conditions": profile.disease_details if profile else None,
        }

        guide_service = get_guide_service()
        content = await guide_service.generate(med_list, user_info)
        guide.content = content
        guide.status = "completed"
        prescription.ocr_status = "guide_completed"
        await guide.save()
        await prescription.save()

    return "fake-job-id"


@pytest.fixture(autouse=True)
async def setup_db():
    await Tortoise.init(
        db_url=TEST_DB_URL,
        modules={
            "models": [
                "app.models.user",
                "app.models.auth_provider",
                "app.models.terms_consent",
                "app.models.patient_profile",
                "app.models.caregiver_patient",
                "app.models.prescription",
                "app.models.schedule",
                "app.models.notification",
                "app.models.audit",
                "app.models.guide",
                "app.models.chat",
            ]
        },
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()


@pytest.fixture(autouse=True)
def mock_enqueue():
    with (
        patch("app.api.prescriptions.enqueue", side_effect=_fake_enqueue),
        patch("app.api.guides.enqueue", side_effect=_fake_enqueue),
        patch("app.api.chat.enqueue", side_effect=_fake_enqueue),
    ):
        yield


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
        "role": "PATIENT",
        "terms_of_service": True,
        "privacy_policy": True,
    }
    await client.post("/api/auth/signup", json=signup_data)
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Test1234!"},
    )
    token = login_resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


class FakeRedis:
    """테스트용 in-memory Redis mock."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        if key in self._store:
            del self._store[key]
            return 1
        return 0


_fake_redis = FakeRedis()


@pytest.fixture(autouse=True)
def fake_redis_cleanup():
    """매 테스트마다 fake_redis store를 초기화."""
    yield _fake_redis
    _fake_redis._store.clear()


@pytest.fixture(autouse=True)
def mock_deps_redis(fake_redis_cleanup):
    """deps.py와 auth.py의 get_state_redis를 공유 FakeRedis로 교체 (JWT blacklist 검증용)."""

    async def _get_fake():
        return fake_redis_cleanup

    with (
        patch("app.core.deps.get_state_redis", side_effect=_get_fake),
        patch("app.api.auth.get_state_redis", side_effect=_get_fake),
    ):
        yield


@pytest.fixture(autouse=True)
def disable_rate_limiter():
    """테스트 환경에서 rate limiter 비활성화."""
    limiter.enabled = False
    yield
    limiter.enabled = True
