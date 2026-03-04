from fastapi import APIRouter

from app.apis.v1.auth_routers import auth_router
from app.apis.v1.guide_routers import (
    adherence_router,
    guide_router,
    schedule_instance_router,
    schedule_router,
)
from app.apis.v1.prescription_routers import medication_router, prescription_router
from app.apis.v1.social_routers import (
    audit_router,
    caregiver_router,
    chat_router,
    notification_router,
)
from app.apis.v1.user_routers import user_router

# 기준: docs/dev/api_spec.md — prefix: /api
v1_routers = APIRouter(prefix="/api")

# AUTH / USER
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)

# PRESCRIPTION / OCR / MEDICATION
v1_routers.include_router(prescription_router)
v1_routers.include_router(medication_router)

# GUIDE / SCHEDULE / ADHERENCE
v1_routers.include_router(guide_router)
v1_routers.include_router(schedule_router)
v1_routers.include_router(schedule_instance_router)
v1_routers.include_router(adherence_router)

# CAREGIVER / CHAT / NOTIFICATION / AUDIT
v1_routers.include_router(caregiver_router)
v1_routers.include_router(chat_router)
v1_routers.include_router(notification_router)
v1_routers.include_router(audit_router)
