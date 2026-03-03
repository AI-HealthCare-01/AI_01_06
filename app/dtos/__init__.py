"""
dtos 패키지 공개 인터페이스.

실제 존재하는 클래스만 export합니다.
각 도메인 모듈을 직접 import하는 것을 권장합니다.
"""

from app.dtos.audit import AuditLogItem, AuditLogListResponse
from app.dtos.auth import LoginRequest, LoginResponse, SignUpRequest, TokenRefreshResponse
from app.dtos.base import BaseSerializerModel, GenericResponse
from app.dtos.caregiver import CaregiverMappingResponse, CaregiverRequestBody
from app.dtos.chat import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatMessageListResponse,
    ChatMessageSendRequest,
    ChatMessageSendResponse,
    ChatMessageSummary,
    ChatThreadCreateRequest,
    ChatThreadListResponse,
    ChatThreadResponse,
)
from app.dtos.guide import GuideResponse
from app.dtos.medication import (
    AdherenceLogRequest,
    AdherenceLogResponse,
    AdherenceSkipRequest,
    MedicationDetailResponse,
    MedicationListResponse,
    ScheduleCreateRequest,
    ScheduleResponse,
)
from app.dtos.notification import NotificationItem, NotificationListResponse
from app.dtos.prescription import (
    OcrResultResponse,
    OcrUpdateRequest,
    PrescriptionDetailResponse,
    PrescriptionListResponse,
    PrescriptionUploadResponse,
)
from app.dtos.users import AccessibilityUpdateRequest, UserInfoResponse, UserUpdateRequest

__all__ = [
    # base
    "BaseSerializerModel",
    "GenericResponse",
    # auth
    "SignUpRequest",
    "LoginRequest",
    "LoginResponse",
    "TokenRefreshResponse",
    # users
    "UserUpdateRequest",
    "AccessibilityUpdateRequest",
    "UserInfoResponse",
    # prescription
    "PrescriptionUploadResponse",
    "PrescriptionDetailResponse",
    "PrescriptionListResponse",
    "OcrResultResponse",
    "OcrUpdateRequest",
    # medication/schedule/adherence
    "MedicationDetailResponse",
    "MedicationListResponse",
    "ScheduleCreateRequest",
    "ScheduleResponse",
    "AdherenceLogRequest",
    "AdherenceSkipRequest",
    "AdherenceLogResponse",
    # guide
    "GuideResponse",
    # caregiver
    "CaregiverRequestBody",
    "CaregiverMappingResponse",
    # chat
    "ChatThreadCreateRequest",
    "ChatThreadResponse",
    "ChatThreadListResponse",
    "ChatMessageSendRequest",
    "ChatMessageSendResponse",
    "ChatMessageSummary",
    "ChatMessageListResponse",
    "ChatFeedbackRequest",
    "ChatFeedbackResponse",
    # notification
    "NotificationItem",
    "NotificationListResponse",
    # audit
    "AuditLogItem",
    "AuditLogListResponse",
]
