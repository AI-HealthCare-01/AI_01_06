import io
from datetime import date

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_schedule_for_medication(auth_client: AsyncClient):
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]

    today = date.today().isoformat()
    resp = await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "MORNING", "start_date": today, "end_date": today}],
    )
    assert resp.json()["success"] is True
    assert resp.json()["data"][0]["time_of_day"] == "MORNING"


@pytest.mark.asyncio
async def test_log_adherence(auth_client: AsyncClient):
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]

    today = date.today().isoformat()
    schedule_resp = await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "NOON", "start_date": today, "end_date": today}],
    )
    sid = schedule_resp.json()["data"][0]["id"]

    log_resp = await auth_client.post(
        f"/api/schedules/{sid}/log",
        json={"target_date": today, "status": "TAKEN"},
    )
    assert log_resp.json()["success"] is True
    assert log_resp.json()["data"]["status"] == "TAKEN"


@pytest.mark.asyncio
async def test_get_today_schedules(auth_client: AsyncClient):
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]

    today = date.today().isoformat()
    await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "EVENING", "start_date": today, "end_date": today}],
    )

    resp = await auth_client.get("/api/schedules/today")
    assert resp.json()["success"] is True
    data = resp.json()["data"]
    assert len(data) >= 1
    # 신규 필드 존재 확인
    assert "today_status" in data[0]
    assert "dosage" in data[0]


@pytest.mark.asyncio
async def test_schedule_invalid_time_of_day(auth_client: AsyncClient):
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]

    resp = await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "INVALID"}],
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_today_schedules_only_returns_own_user_schedules(auth_client: AsyncClient, client: AsyncClient):
    """OWASP A01 IDOR: 다른 유저의 스케줄이 today에 노출되지 않는다."""
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]
    today = date.today().isoformat()
    await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "MORNING", "start_date": today, "end_date": today}],
    )

    # user B 신규 가입 → today 조회 → 빈 결과여야 함
    await client.post(
        "/api/auth/signup",
        json={
            "email": "b_isolation@example.com",
            "password": "Test1234!",
            "nickname": "B격리유저",
            "name": "김을지",
            "role": "PATIENT",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    login_b = await client.post("/api/auth/login", json={"email": "b_isolation@example.com", "password": "Test1234!"})
    token_b = login_b.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token_b}"

    resp = await client.get("/api/schedules/today")
    assert resp.json()["success"] is True
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_today_schedules_includes_today_status(auth_client: AsyncClient):
    """today_status: 기록 전 None → TAKEN 기록 후 'TAKEN'."""
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]
    today = date.today().isoformat()
    schedule_resp = await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "MORNING", "start_date": today, "end_date": today}],
    )
    sid = schedule_resp.json()["data"][0]["id"]

    resp = await auth_client.get("/api/schedules/today")
    items = resp.json()["data"]
    target = next((item for item in items if item["id"] == sid), None)
    assert target is not None
    assert target["today_status"] is None

    await auth_client.post(f"/api/schedules/{sid}/log", json={"target_date": today, "status": "TAKEN"})

    resp2 = await auth_client.get("/api/schedules/today")
    items2 = resp2.json()["data"]
    target2 = next((item for item in items2 if item["id"] == sid), None)
    assert target2 is not None
    assert target2["today_status"] == "TAKEN"


@pytest.mark.asyncio
async def test_get_schedule_logs_forbidden_for_other_user(auth_client: AsyncClient, client: AsyncClient):
    """다른 유저가 스케줄 로그를 조회할 수 없다."""
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]
    today = date.today().isoformat()
    schedule_resp = await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "MORNING", "start_date": today, "end_date": today}],
    )
    sid = schedule_resp.json()["data"][0]["id"]

    await client.post(
        "/api/auth/signup",
        json={
            "email": "c_forbidden@example.com",
            "password": "Test1234!",
            "nickname": "C권한유저",
            "name": "박을지",
            "role": "PATIENT",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    login_c = await client.post("/api/auth/login", json={"email": "c_forbidden@example.com", "password": "Test1234!"})
    token_c = login_c.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token_c}"

    resp = await client.get(f"/api/schedules/{sid}/logs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_schedule_for_other_user_medication_forbidden(auth_client: AsyncClient, client: AsyncClient):
    """OWASP A01 IDOR: 다른 유저의 약물로 스케줄 생성이 403을 반환해야 한다."""
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    victim_mid = meds.json()["data"][0]["id"]

    await client.post(
        "/api/auth/signup",
        json={
            "email": "d_attacker@example.com",
            "password": "Test1234!",
            "nickname": "D공격자",
            "name": "이을지",
            "role": "PATIENT",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    login_d = await client.post("/api/auth/login", json={"email": "d_attacker@example.com", "password": "Test1234!"})
    token_d = login_d.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token_d}"

    today = date.today().isoformat()
    resp = await client.post(
        "/api/schedules",
        json=[{"medication_id": victim_mid, "time_of_day": "MORNING", "start_date": today, "end_date": today}],
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_log_adherence_for_other_user_schedule_forbidden(auth_client: AsyncClient, client: AsyncClient):
    """OWASP A01 IDOR: 다른 유저의 스케줄에 복약 기록이 403을 반환해야 한다."""
    image = io.BytesIO(b"fake")
    upload = await auth_client.post("/api/prescriptions", files={"file": ("t.png", image, "image/png")})
    pid = upload.json()["data"]["id"]
    meds = await auth_client.get(f"/api/prescriptions/{pid}/medications")
    mid = meds.json()["data"][0]["id"]
    today = date.today().isoformat()
    schedule_resp = await auth_client.post(
        "/api/schedules",
        json=[{"medication_id": mid, "time_of_day": "MORNING", "start_date": today, "end_date": today}],
    )
    victim_sid = schedule_resp.json()["data"][0]["id"]

    await client.post(
        "/api/auth/signup",
        json={
            "email": "e_attacker@example.com",
            "password": "Test1234!",
            "nickname": "E공격자",
            "name": "최을지",
            "role": "PATIENT",
            "terms_of_service": True,
            "privacy_policy": True,
        },
    )
    login_e = await client.post("/api/auth/login", json={"email": "e_attacker@example.com", "password": "Test1234!"})
    token_e = login_e.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token_e}"

    resp = await client.post(
        f"/api/schedules/{victim_sid}/log",
        json={"target_date": today, "status": "TAKEN"},
    )
    assert resp.status_code == 403
