import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

from app.api import (
    auth,
    caregivers,
    chat,
    google_auth,
    guides,
    kakao_auth,
    medications,
    notifications,
    prescriptions,
    schedules,
    users,
)
from app.core.database import TORTOISE_ORM

app = FastAPI(title="Project & Sullivan API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(kakao_auth.router)
app.include_router(google_auth.router)
app.include_router(users.router)
app.include_router(prescriptions.router)
app.include_router(medications.router)
app.include_router(guides.router)
app.include_router(caregivers.router)
app.include_router(schedules.router)
app.include_router(notifications.router)
app.include_router(chat.router)

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get("/api/health")
async def health_check():
    return {"success": True, "data": {"status": "ok"}, "error": None}
