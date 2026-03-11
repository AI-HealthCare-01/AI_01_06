import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ocr_upload_and_result(auth_client: AsyncClient):
    """처방전 업로드 후 OCR 결과가 정상 구조로 반환되는지 확인."""
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("prescription.png", fake_image, "image/png")},
    )
    assert upload_resp.status_code == 200
    upload_body = upload_resp.json()
    assert upload_body["success"] is True

    pid = upload_body["data"]["id"]

    ocr_resp = await auth_client.get(f"/api/prescriptions/{pid}/ocr")
    assert ocr_resp.status_code == 200
    ocr = ocr_resp.json()["data"]

    assert ocr["hospital_name"] is not None
    assert ocr["doctor_name"] is not None
    assert ocr["prescription_date"] is not None
    assert isinstance(ocr["medications"], list)
    assert len(ocr["medications"]) > 0


@pytest.mark.asyncio
async def test_ocr_medications_have_required_fields(auth_client: AsyncClient):
    """OCR로 추출된 약품에 name, dosage, instructions 필드가 있는지 확인."""
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("prescription.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    ocr_resp = await auth_client.get(f"/api/prescriptions/{pid}/ocr")
    medications = ocr_resp.json()["data"]["medications"]

    for med in medications:
        assert "name" in med, f"name 필드 없음: {med}"
        assert "dosage" in med, f"dosage 필드 없음: {med}"
        assert "instructions" in med, f"instructions 필드 없음: {med}"


@pytest.mark.asyncio
async def test_ocr_status_is_completed(auth_client: AsyncClient):
    """처방전 업로드 후 OCR 처리가 완료 상태인지 확인."""
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("prescription.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    detail_resp = await auth_client.get(f"/api/prescriptions/{pid}")
    assert detail_resp.json()["data"]["ocr_status"] == "ocr_completed"
