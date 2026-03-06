from unittest.mock import patch

import pytest
from app.main import app
from app.models.guide import Guide
from app.models.prescription import Medication, Prescription
from app.models.user import User
from app.services.guide_service import get_guide_service
from app.services.ocr_service import get_ocr_service
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

TEST_DB_URL = "sqlite://:memory:"


async def _fake_enqueue(task_name: str, *args, **kwargs) -> str:
    """Simulate worker inline: run OCR/guide synchronously for tests."""
    if task_name == "ocr_task":
        prescription_id = args[0]
        prescription = await Prescription.get(id=prescription_id)
        ocr_service = get_ocr_service()
        ocr_result = await ocr_service.extract(prescription.image_path)

        prescription.hospital_name = ocr_result.get("hospital_name")
        prescription.doctor_name = ocr_result.get("doctor_name")
        prescription.prescription_date = ocr_result.get("prescription_date")
        prescription.diagnosis = ocr_result.get("diagnosis")
        prescription.ocr_raw = ocr_result
        prescription.ocr_status = "completed"
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
        user_info = {
            "name": user.name,
            "height": user.height,
            "weight": user.weight,
            "allergies": user.allergies,
            "conditions": user.conditions,
        }

        guide_service = get_guide_service()
        content = await guide_service.generate(med_list, user_info)
        guide.content = content
        guide.status = "completed"
        await guide.save()

    return "fake-job-id"


@pytest.fixture(autouse=True)
async def setup_db():
    await Tortoise.init(
        db_url=TEST_DB_URL,
        modules={"models": ["app.models.user", "app.models.prescription", "app.models.guide"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()


@pytest.fixture(autouse=True)
def mock_enqueue():
    with (
        patch("app.api.prescriptions.enqueue", side_effect=_fake_enqueue),
        patch("app.api.guides.enqueue", side_effect=_fake_enqueue),
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
