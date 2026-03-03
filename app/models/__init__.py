"""
models 패키지 공개 인터페이스.

Tortoise ORM이 모델을 자동 탐색할 수 있도록 모든 모델을 여기서 export합니다.
"""

from app.models.audits import AuditLog
from app.models.chats import ChatFeedback, ChatMessage, ChatSession
from app.models.guides import GuideMedicationCard, MedicationGuide
from app.models.medicals import (
    AdherenceLog,
    Medication,
    MedicationSchedule,
    OcrJob,
    Prescription,
    PrescriptionImage,
)
from app.models.notifications import Notification, NotificationSetting
from app.models.users import (
    AccessibilitySetting,
    AuthProviderModel,
    CaregiverPatientMapping,
    PatientProfile,
    TermsConsent,
    User,
)

__all__ = [
    # users
    "User",
    "AuthProviderModel",
    "PatientProfile",
    "CaregiverPatientMapping",
    "TermsConsent",
    "AccessibilitySetting",
    # medicals
    "Prescription",
    "PrescriptionImage",
    "Medication",
    "MedicationSchedule",
    "AdherenceLog",
    "OcrJob",
    # guides
    "MedicationGuide",
    "GuideMedicationCard",
    # chats
    "ChatSession",
    "ChatMessage",
    "ChatFeedback",
    # notifications
    "Notification",
    "NotificationSetting",
    # audits
    "AuditLog",
]
