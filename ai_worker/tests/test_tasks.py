import pytest
from app.models.guide import Guide
from app.models.prescription import Medication, Prescription
from app.models.user import User
from worker.tasks.guide_task import guide_task
from worker.tasks.ocr_task import ocr_task


@pytest.fixture
async def user():
    return await User.create(
        email="test@example.com",
        nickname="테스트",
        password_hash="fakehash",
        name="홍길동",
        role="patient",
    )


@pytest.fixture
async def prescription(user):
    return await Prescription.create(
        user=user,
        image_path="uploads/test.png",
        ocr_status="processing",
    )


async def test_ocr_task_completes_prescription(prescription):
    await ocr_task({}, prescription.id)

    updated = await Prescription.get(id=prescription.id)
    assert updated.ocr_status == "completed"
    assert updated.hospital_name == "서울대학교병원"

    meds = await Medication.filter(prescription=updated)
    assert len(meds) == 2


async def test_guide_task_generates_content(user, prescription):
    # First complete OCR so medications exist
    await ocr_task({}, prescription.id)

    guide = await Guide.create(user=user, prescription=prescription, status="generating")
    await guide_task({}, guide.id, user.id)

    updated = await Guide.get(id=guide.id)
    assert updated.status == "completed"
    assert "medication_guides" in updated.content
    assert "disclaimer" in updated.content
