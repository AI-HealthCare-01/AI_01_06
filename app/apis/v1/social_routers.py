"""
CAREGIVER / CHAT / NOTIFICATION / AUDIT 도메인 라우터.

기준: docs/dev/api_spec.md
  POST   /api/caregivers/requests
  GET    /api/caregivers/requests/inbox
  PATCH  /api/caregivers/requests/{request_id}/approve
  PATCH  /api/caregivers/requests/{request_id}/reject
  GET    /api/caregivers/patients
  DELETE /api/caregivers/patients/{mapping_id}
  GET    /api/chat/threads
  POST   /api/chat/threads
  POST   /api/chat/messages
  GET    /api/chat/threads/{thread_id}/messages
  POST   /api/chat/feedback
  GET    /api/notifications
  PATCH  /api/notifications/{notification_id}/read
  PATCH  /api/notifications/read-all
  GET    /api/admin/audit
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response

from app.core.enums import CaregiverMappingStatus, SenderType
from app.dependencies.security import get_request_user
from app.dtos.audit import AuditLogItem
from app.dtos.caregiver import CaregiverRequestBody
from app.dtos.chat import (
    ChatFeedbackRequest,
    ChatMessageSendRequest,
    ChatThreadCreateRequest,
)
from app.dtos.notification import NotificationItem
from app.models.users import User
from app.repositories.social_repository import (
    AuditRepository,
    CaregiverRepository,
    ChatRepository,
    NotificationRepository,
)

caregiver_router = APIRouter(prefix="/caregivers", tags=["caregivers"])
chat_router = APIRouter(prefix="/chat", tags=["chat"])
notification_router = APIRouter(prefix="/notifications", tags=["notifications"])
audit_router = APIRouter(prefix="/admin/audit", tags=["audit"])

_caregiver_repo = CaregiverRepository()
_chat_repo = ChatRepository()
_notification_repo = NotificationRepository()
_audit_repo = AuditRepository()


# ── CAREGIVER ──────────────────────────────────

@caregiver_router.post("/requests", status_code=status.HTTP_201_CREATED)
async def request_caregiver(
    body: CaregiverRequestBody,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-USR-020: 보호자가 환자 연동 요청."""
    existing = await _caregiver_repo.get_mapping(user.id, body.patient_id)
    if existing and existing.status == CaregiverMappingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 연동 요청 중입니다.")
    mapping = await _caregiver_repo.request(user.id, body.patient_id)
    return Response(content={"status": mapping.status}, status_code=status.HTTP_201_CREATED)


@caregiver_router.get("/requests/inbox", status_code=status.HTTP_200_OK)
async def list_caregiver_inbox(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    mappings = await _caregiver_repo.list_inbox(user.id)
    return Response(content={"requests": [{"caregiver_id": m.caregiver_id, "requested_at": str(m.requested_at)} for m in mappings]}, status_code=status.HTTP_200_OK)


@caregiver_router.patch("/requests/{caregiver_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
async def approve_caregiver(
    caregiver_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    mapping = await _caregiver_repo.get_mapping(caregiver_id, user.id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="연동 요청을 찾을 수 없습니다.")
    await _caregiver_repo.update_status(mapping, CaregiverMappingStatus.APPROVED)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


@caregiver_router.patch("/requests/{caregiver_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_caregiver(
    caregiver_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    mapping = await _caregiver_repo.get_mapping(caregiver_id, user.id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="연동 요청을 찾을 수 없습니다.")
    await _caregiver_repo.update_status(mapping, CaregiverMappingStatus.REJECTED)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


@caregiver_router.get("/patients", status_code=status.HTTP_200_OK)
async def list_my_patients(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    mappings = await _caregiver_repo.list_patients(user.id)
    return Response(content={"patients": [{"patient_id": m.patient_id} for m in mappings]}, status_code=status.HTTP_200_OK)


@caregiver_router.delete("/patients/{mapping_patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_patient(
    mapping_patient_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    mapping = await _caregiver_repo.get_mapping(user.id, mapping_patient_id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="연동 정보를 찾을 수 없습니다.")
    await _caregiver_repo.update_status(mapping, CaregiverMappingStatus.REVOKED)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


# ── CHAT ──────────────────────────────────

@chat_router.get("/threads", status_code=status.HTTP_200_OK)
async def list_threads(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-CHAT-001: 챗봇 대화방 목록 조회."""
    sessions = await _chat_repo.list_sessions(user.id)
    data = [{"id": s.id, "started_at": str(s.started_at), "is_active": s.is_active} for s in sessions]
    return Response(content={"threads": data}, status_code=status.HTTP_200_OK)


@chat_router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_thread(
    body: ChatThreadCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    session = await _chat_repo.create_session(patient_id=user.id)
    return Response(content={"id": session.id}, status_code=status.HTTP_201_CREATED)


@chat_router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    body: ChatMessageSendRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-CHAT-002: 메시지 전송 (LLM 응답은 ai_worker 연동 예정)."""
    msg = await _chat_repo.add_message(
        session_id=body.thread_id,
        sender_type=SenderType.USER,
        message_text=body.message,
    )
    return Response(content={"message_id": msg.id, "created_at": str(msg.created_at)}, status_code=status.HTTP_201_CREATED)


@chat_router.get("/threads/{thread_id}/messages", status_code=status.HTTP_200_OK)
async def list_messages(
    thread_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    messages = await _chat_repo.list_messages(thread_id)
    data = [{"id": m.id, "sender_type": m.sender_type, "message_text": m.message_text, "created_at": str(m.created_at)} for m in messages]
    return Response(content={"messages": data}, status_code=status.HTTP_200_OK)


@chat_router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def chat_feedback(
    body: ChatFeedbackRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    fb = await _chat_repo.add_feedback(
        message_id=body.message_id,
        feedback_category=body.rating,
        additional_notes=body.comment,
    )
    return Response(content={"feedback_id": fb.id}, status_code=status.HTTP_201_CREATED)


# ── NOTIFICATION ──────────────────────────────────

@notification_router.get("", status_code=status.HTTP_200_OK)
async def list_notifications(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    """REQ-COM-002: 알림 목록 조회."""
    items = await _notification_repo.list_by_user(user.id)
    data = [NotificationItem.model_validate(n).model_dump(mode="json") for n in items]
    return Response(content={"notifications": data}, status_code=status.HTTP_200_OK)


@notification_router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def read_all_notifications(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    await _notification_repo.mark_all_read(user.id)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


@notification_router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def read_notification(
    notification_id: str,
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    n = await _notification_repo.get_by_id(notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
    await _notification_repo.mark_read(n)
    return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)


# ── AUDIT ──────────────────────────────────

@audit_router.get("", status_code=status.HTTP_200_OK)
async def list_audit_logs(
    user: Annotated[User, Depends(get_request_user)],
    limit: int = 100,
    offset: int = 0,
) -> Response:
    """감사 로그 조회 (ADMIN 전용)."""
    logs = await _audit_repo.list_all(limit=limit, offset=offset)
    data = [AuditLogItem.model_validate(log).model_dump(mode="json") for log in logs]
    return Response(content={"logs": data, "total": len(data)}, status_code=status.HTTP_200_OK)
