import logging
from datetime import UTC, datetime, timedelta

from tortoise.transactions import in_transaction

from app.models.audit import AuditLog
from app.models.auth_provider import AuthProvider
from app.models.caregiver_patient import CaregiverPatientMapping
from app.models.chat import ChatFeedback, ChatMessage, ChatThread
from app.models.guide import Guide
from app.models.notification import Notification, NotificationSetting
from app.models.patient_profile import PatientProfile
from app.models.prescription import Medication, Prescription
from app.models.schedule import AdherenceLog, MedicationSchedule
from app.models.terms_consent import TermsConsent
from app.models.user import User

logger = logging.getLogger(__name__)

_RETENTION_DAYS = 30


async def purge_deleted_users(ctx: dict) -> int:
    """소프트 삭제 후 30일 경과된 계정을 물리 삭제한다.

    PIPA 2025: 정보주체 삭제 요청 후 파기 의무.
    soft-delete 30일 후 물리 삭제로 법적 요건 충족.
    """
    cutoff = datetime.now(UTC) - timedelta(days=_RETENTION_DAYS)
    expired_users = await User.filter(deleted_at__isnull=False, deleted_at__lt=cutoff)

    count = 0
    for user in expired_users:
        async with in_transaction():
            prescriptions = await Prescription.filter(user_id=user.id)
            prescription_ids = [p.id for p in prescriptions]

            if prescription_ids:
                threads = await ChatThread.filter(user_id=user.id)
                thread_ids = [t.id for t in threads]
                if thread_ids:
                    await ChatFeedback.filter(thread_id__in=thread_ids).delete()
                    await ChatMessage.filter(thread_id__in=thread_ids).delete()
                await ChatThread.filter(user_id=user.id).delete()

                medications = await Medication.filter(prescription_id__in=prescription_ids)
                medication_ids = [m.id for m in medications]
                if medication_ids:
                    await AdherenceLog.filter(schedule__medication_id__in=medication_ids).delete()
                    await MedicationSchedule.filter(medication_id__in=medication_ids).delete()

                await Guide.filter(user_id=user.id).delete()
                await Medication.filter(prescription_id__in=prescription_ids).delete()
                await Prescription.filter(user_id=user.id).delete()
            else:
                await ChatThread.filter(user_id=user.id).delete()

            await AdherenceLog.filter(actor_user_id=user.id).delete()
            await AuditLog.filter(actor_id=user.id).delete()
            await Notification.filter(user_id=user.id).delete()
            await NotificationSetting.filter(user_id=user.id).delete()
            await CaregiverPatientMapping.filter(caregiver_id=user.id).delete()
            await CaregiverPatientMapping.filter(patient_id=user.id).delete()
            await AuthProvider.filter(user_id=user.id).delete()
            await PatientProfile.filter(user_id=user.id).delete()
            await TermsConsent.filter(user_id=user.id).delete()
            await user.delete()
        count += 1

    if count > 0:
        logger.info("purge_deleted_users: %d 계정 물리 삭제 완료", count)

    return count
