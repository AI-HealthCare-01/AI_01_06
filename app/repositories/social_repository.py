"""
CAREGIVER / CHAT / NOTIFICATION / AUDIT 도메인 Repository.
"""

import uuid
from datetime import UTC

from app.core.enums import AuditOutcome, CaregiverMappingStatus
from app.models.audits import AuditLog
from app.models.chats import ChatFeedback, ChatMessage, ChatSession
from app.models.notifications import Notification
from app.models.users import CaregiverPatientMapping


class CaregiverRepository:
    async def get_mapping(self, caregiver_id: str, patient_id: str) -> CaregiverPatientMapping | None:
        return await CaregiverPatientMapping.get_or_none(caregiver_id=caregiver_id, patient_id=patient_id)

    async def request(self, caregiver_id: str, patient_id: str) -> CaregiverPatientMapping:
        return await CaregiverPatientMapping.create(
            caregiver_id=caregiver_id,
            patient_id=patient_id,
            status=CaregiverMappingStatus.PENDING,
        )

    async def list_inbox(self, patient_id: str) -> list[CaregiverPatientMapping]:
        return await CaregiverPatientMapping.filter(patient_id=patient_id, status=CaregiverMappingStatus.PENDING)

    async def list_patients(self, caregiver_id: str) -> list[CaregiverPatientMapping]:
        return await CaregiverPatientMapping.filter(caregiver_id=caregiver_id, status=CaregiverMappingStatus.APPROVED)

    async def update_status(self, mapping: CaregiverPatientMapping, status: CaregiverMappingStatus) -> None:
        mapping.status = status
        await mapping.save(update_fields=["status"])


class ChatRepository:
    async def list_sessions(self, patient_id: str) -> list[ChatSession]:
        return await ChatSession.filter(patient_id=patient_id).order_by("-started_at")

    async def create_session(self, *, patient_id: str, prescription_id: str | None = None, guide_id: str | None = None) -> ChatSession:
        return await ChatSession.create(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            prescription_id=prescription_id,
            guide_id=guide_id,
        )

    async def list_messages(self, session_id: str) -> list[ChatMessage]:
        return await ChatMessage.filter(session_id=session_id).order_by("created_at")

    async def add_message(self, *, session_id: str, sender_type: str, message_text: str) -> ChatMessage:
        return await ChatMessage.create(
            id=str(uuid.uuid4()),
            session_id=session_id,
            sender_type=sender_type,
            message_text=message_text,
        )

    async def add_feedback(self, *, message_id: str, feedback_category: str, additional_notes: str | None = None) -> ChatFeedback:
        return await ChatFeedback.create(
            id=str(uuid.uuid4()),
            message_id=message_id,
            feedback_category=feedback_category,
            additional_notes=additional_notes,
        )


class NotificationRepository:
    async def list_by_user(self, user_id: str) -> list[Notification]:
        return await Notification.filter(user_id=user_id).order_by("-created_at")

    async def get_by_id(self, notification_id: str) -> Notification | None:
        return await Notification.get_or_none(id=notification_id)

    async def mark_read(self, notification: Notification) -> None:
        from datetime import datetime
        notification.is_read = True
        notification.read_at = datetime.now(tz=UTC)
        await notification.save(update_fields=["is_read", "read_at"])

    async def mark_all_read(self, user_id: str) -> None:
        from datetime import datetime
        await Notification.filter(user_id=user_id, is_read=False).update(
            is_read=True, read_at=datetime.now(tz=UTC)
        )


class AuditRepository:
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return await AuditLog.all().order_by("-created_at").offset(offset).limit(limit)

    async def create(
        self,
        *,
        actor_id: str,
        action_type: str,
        resource_type: str | None,
        resource_id: str | None,
        ip_address: str,
        outcome: AuditOutcome,
    ) -> AuditLog:
        return await AuditLog.create(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            outcome=outcome,
        )
