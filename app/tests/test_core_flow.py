"""핵심 E2E 플로우 테스트:
처방전 업로드 → OCR → 수정 → 가이드 생성 → 가이드 조회
(signup/login 단독 검증은 test_auth.py 참고)
"""

import importlib
import io

import pytest
from httpx import AsyncClient

import app.api.prescriptions as prescriptions_api


def test_upload_dir_from_env(monkeypatch):
    """UPLOAD_DIR 환경변수가 주입되면 해당 경로를 사용한다."""
    monkeypatch.setenv("UPLOAD_DIR", "/tmp/test_uploads")
    importlib.reload(prescriptions_api)
    assert prescriptions_api.UPLOAD_DIR == "/tmp/test_uploads"
    # 정리: 기본값으로 복원
    monkeypatch.delenv("UPLOAD_DIR")
    importlib.reload(prescriptions_api)


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_prescription_triggers_ocr(auth_client: AsyncClient):
    fake_image = io.BytesIO(b"fake image content")
    resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["ocr_status"] == "processing"


@pytest.mark.asyncio
async def test_get_ocr_result(auth_client: AsyncClient):
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    resp = await auth_client.get(f"/api/prescriptions/{pid}/ocr")
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["hospital_name"] == "서울대학교병원"
    assert len(body["data"]["medications"]) == 2


@pytest.mark.asyncio
async def test_update_ocr_result(auth_client: AsyncClient):
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    resp = await auth_client.put(
        f"/api/prescriptions/{pid}/ocr",
        json={
            "hospital_name": "수정병원",
            "doctor_name": "박의사",
            "prescription_date": "2026-03-01",
            "diagnosis": "감기",
            "medications": [
                {"name": "타이레놀", "dosage": "500mg", "frequency": "1일 3회"},
            ],
        },
    )
    assert resp.json()["success"] is True

    ocr_body = (await auth_client.get(f"/api/prescriptions/{pid}/ocr")).json()
    assert ocr_body["data"]["hospital_name"] == "수정병원"
    assert len(ocr_body["data"]["medications"]) == 1


@pytest.mark.asyncio
async def test_create_guide(auth_client: AsyncClient):
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    resp = await auth_client.post("/api/guides", json={"prescription_id": pid})
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] in ("generating", "completed")


@pytest.mark.asyncio
async def test_get_guide(auth_client: AsyncClient):
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    create_resp = await auth_client.post("/api/guides", json={"prescription_id": pid})
    guide_id = create_resp.json()["data"]["id"]

    resp = await auth_client.get(f"/api/guides/{guide_id}")
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["prescription_info"]["hospital_name"] == "서울대학교병원"
    assert "disclaimer" in body["data"]["content"]


@pytest.mark.asyncio
async def test_get_guide_profile_not_updated_when_unchanged(auth_client: AsyncClient):
    """프로필을 변경하지 않았으면 profile_updated는 False여야 한다."""
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    create_resp = await auth_client.post("/api/guides", json={"prescription_id": pid})
    guide_id = create_resp.json()["data"]["id"]

    resp = await auth_client.get(f"/api/guides/{guide_id}")
    body = resp.json()
    assert body["data"]["profile_updated"] is False


@pytest.mark.asyncio
async def test_get_guide_profile_updated_when_changed(auth_client: AsyncClient):
    """프로필 변경 후 기존 가이드 조회 시 profile_updated는 True여야 한다."""
    fake_image = io.BytesIO(b"fake image content")
    upload_resp = await auth_client.post(
        "/api/prescriptions",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    pid = upload_resp.json()["data"]["id"]

    create_resp = await auth_client.post("/api/guides", json={"prescription_id": pid})
    guide_id = create_resp.json()["data"]["id"]

    await auth_client.patch("/api/users/me", json={"height_cm": 180.0})

    resp = await auth_client.get(f"/api/guides/{guide_id}")
    body = resp.json()
    assert body["data"]["profile_updated"] is True
