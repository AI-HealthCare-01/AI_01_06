"""핵심 E2E 플로우 테스트:
1. 회원가입 + 로그인
2. 처방전 업로드 (OCR 자동 실행)
3. OCR 결과 조회
4. OCR 결과 수정/확정
5. 복약 가이드 생성
6. 복약 가이드 조회
"""

import importlib
import io

import app.api.prescriptions as prescriptions_api
import pytest
from httpx import AsyncClient


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
async def test_signup_returns_user_info(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        json={
            "email": "user@test.com",
            "password": "Pass1234!",
            "nickname": "닉네임",
            "name": "테스트",
            "role": "patient",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == "user@test.com"


@pytest.mark.asyncio
async def test_login_returns_tokens(client: AsyncClient):
    await client.post(
        "/api/auth/signup",
        json={
            "email": "user@test.com",
            "password": "Pass1234!",
            "nickname": "닉네임",
            "name": "테스트",
            "role": "patient",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    resp = await client.post(
        "/api/auth/login",
        json={
            "email": "user@test.com",
            "password": "Pass1234!",
        },
    )
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


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
    body = resp.json()
    assert body["success"] is True

    ocr_resp = await auth_client.get(f"/api/prescriptions/{pid}/ocr")
    ocr_body = ocr_resp.json()
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
