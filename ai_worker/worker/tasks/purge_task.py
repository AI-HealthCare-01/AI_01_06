import logging
from datetime import UTC, datetime, timedelta

from app.models.auth_provider import AuthProvider
from app.models.patient_profile import PatientProfile
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
        await AuthProvider.filter(user_id=user.id).delete()
        await PatientProfile.filter(user_id=user.id).delete()
        await TermsConsent.filter(user_id=user.id).delete()
        await user.delete()
        count += 1

    if count > 0:
        logger.info("purge_deleted_users: %d 계정 물리 삭제 완료", count)

    return count
