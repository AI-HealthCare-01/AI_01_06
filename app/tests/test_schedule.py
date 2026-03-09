import io
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.models.schedule import AdherenceLog, MedicationSchedule


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

    schedule = await MedicationSchedule.get(id=sid)
    logs = await AdherenceLog.filter(schedule=schedule)
    assert len(logs) == 1


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
    assert len(resp.json()["data"]) >= 1


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
