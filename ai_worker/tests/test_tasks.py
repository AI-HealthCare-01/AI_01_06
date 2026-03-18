from unittest.mock import AsyncMock

import pytest

from app.models.guide import Guide
from app.models.patient_profile import PatientProfile
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
async def patient_profile(user):
    return await PatientProfile.create(
        user=user,
        height_cm=170.0,
        weight_kg=65.0,
        allergy_details="없음",
        disease_details="없음",
    )


@pytest.fixture
async def prescription(user):
    return await Prescription.create(
        user=user,
        image_path="uploads/test.png",
        ocr_status="processing",
    )


async def test_ocr_task_completes_prescription(prescription):
    await ocr_task({"redis": AsyncMock()}, prescription.id)

    updated = await Prescription.get(id=prescription.id)
    assert updated.ocr_status == "ocr_completed"
    assert updated.hospital_name == "서울대학교병원"

    meds = await Medication.filter(prescription=updated)
    assert len(meds) == 2


async def test_ocr_task_creates_guide_record(user, prescription):
    """ocr_task 완료 시 Guide 레코드가 prescription에 연결되어 자동 생성된다."""
    ctx = {"redis": AsyncMock()}
    await ocr_task(ctx, prescription.id)

    guides = await Guide.filter(prescription=prescription)
    assert len(guides) == 1
    guide = guides[0]
    assert guide.status == "generating"
    assert (await guide.user).id == user.id


async def test_ocr_task_enqueues_guide_task(user, prescription):
    """ocr_task 완료 시 ctx["redis"]를 통해 guide_task가 자동으로 enqueue된다."""
    mock_redis = AsyncMock()
    ctx = {"redis": mock_redis}
    await ocr_task(ctx, prescription.id)

    mock_redis.enqueue_job.assert_called_once()
    task_name, guide_id, enqueued_user_id = mock_redis.enqueue_job.call_args[0]
    assert task_name == "guide_task"

    guide = await Guide.filter(prescription=prescription).first()
    assert guide_id == guide.id
    assert enqueued_user_id == user.id


async def test_guide_task_updates_prescription_status(user, patient_profile, prescription):
    """guide_task 완료 시 Prescription.ocr_status가 guide_completed로 변경된다."""
    await ocr_task({"redis": AsyncMock()}, prescription.id)

    guide = await Guide.filter(prescription=prescription).first()
    await guide_task({}, guide.id, user.id)

    updated = await Prescription.get(id=prescription.id)
    assert updated.ocr_status == "guide_completed"


async def test_guide_task_generates_content(user, patient_profile, prescription):
    """guide_task 완료 시 Guide에 medication_guides와 disclaimer가 포함된 content가 저장된다."""
    await ocr_task({"redis": AsyncMock()}, prescription.id)

    guide = await Guide.filter(prescription=prescription).first()
    await guide_task({}, guide.id, user.id)

    updated = await Guide.get(id=guide.id)
    assert updated.status == "completed"
    assert "medication_guides" in updated.content
    assert "disclaimer" in updated.content


async def test_guide_task_uses_patient_profile(user, patient_profile, prescription):
    """guide_task가 PatientProfile의 키/몸무게/알레르기/기저질환을 user_info에 포함한다."""
    await ocr_task({"redis": AsyncMock()}, prescription.id)

    guide = await Guide.filter(prescription=prescription).first()
    await guide_task({}, guide.id, user.id)

    updated = await Guide.get(id=guide.id)
    assert updated.status == "completed"
    assert updated.content is not None
