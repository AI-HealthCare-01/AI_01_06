import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from tortoise.contrib.fastapi import register_tortoise

from app import config
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
from app.core.rate_limit import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


app = FastAPI(title="Project & Sullivan API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Acting-For"],
    max_age=600,
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
    generate_schemas=False,
    add_exception_handlers=True,
)


@app.get("/api/health")
async def health_check():
    return {"success": True, "data": {"status": "ok"}, "error": None}
