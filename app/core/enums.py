from enum import Enum

# ──────────────────────────────────────────
# User 도메인
# ──────────────────────────────────────────


class UserRole(str, Enum):
    """users.role — PATIENT | GUARDIAN"""

    PATIENT = "PATIENT"
    GUARDIAN = "GUARDIAN"


class Gender(str, Enum):
    """users.gender — M | F"""

    M = "M"
    F = "F"


class FontSizeMode(str, Enum):
    """users.font_size_mode / accessibility_settings.font_mode — SMALL | LARGE"""

    SMALL = "SMALL"
    LARGE = "LARGE"


# ──────────────────────────────────────────
# Auth 도메인
# ──────────────────────────────────────────


class AuthProvider(str, Enum):
    """auth_providers.provider — LOCAL | KAKAO | NAVER | GOOGLE"""

    LOCAL = "LOCAL"
    KAKAO = "KAKAO"
    NAVER = "NAVER"
    GOOGLE = "GOOGLE"


# ──────────────────────────────────────────
# Caregiver 도메인
# ──────────────────────────────────────────


class CaregiverMappingStatus(str, Enum):
    """caregiver_patient_mappings.status — PENDING | APPROVED | REJECTED | REVOKED"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


# ──────────────────────────────────────────
# Prescription / OCR 도메인
# ──────────────────────────────────────────


class VerificationStatus(str, Enum):
    """prescriptions.verification_status — DRAFT | CONFIRMED"""

    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"


class OcrProvider(str, Enum):
    """ocr_jobs.provider — NAVER_CLOVA | UPSTAGE"""

    NAVER_CLOVA = "NAVER_CLOVA"
    UPSTAGE = "UPSTAGE"


class OcrStatus(str, Enum):
    """ocr_jobs.status — REQUESTED | DONE | FAILED"""

    REQUESTED = "REQUESTED"
    DONE = "DONE"
    FAILED = "FAILED"


# ──────────────────────────────────────────
# Schedule / Adherence 도메인
# ──────────────────────────────────────────


class TimeOfDay(str, Enum):
    """medication_schedules.time_of_day — MORNING | NOON | EVENING | BEDTIME"""

    MORNING = "MORNING"
    NOON = "NOON"
    EVENING = "EVENING"
    BEDTIME = "BEDTIME"


class AdherenceStatus(str, Enum):
    """adherence_logs.status — TAKEN | SKIPPED"""

    TAKEN = "TAKEN"
    SKIPPED = "SKIPPED"


# ──────────────────────────────────────────
# Chat 도메인
# ──────────────────────────────────────────


class SenderType(str, Enum):
    """chat_messages.sender_type — USER | ASSISTANT | SYSTEM"""

    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


# ──────────────────────────────────────────
# Notification 도메인
# ──────────────────────────────────────────


class NotificationType(str, Enum):
    """notifications.type — DOSE_REMINDER | SYSTEM"""

    DOSE_REMINDER = "DOSE_REMINDER"
    SYSTEM = "SYSTEM"


# ──────────────────────────────────────────
# Audit 도메인
# ──────────────────────────────────────────


class AuditOutcome(str, Enum):
    """audit_logs.outcome — SUCCESS | FAIL"""

    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
