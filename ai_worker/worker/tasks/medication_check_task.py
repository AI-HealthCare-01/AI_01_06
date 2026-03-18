from app.services.notification_service import check_missed_medications


async def medication_check_cron(ctx: dict) -> None:
    """ARQ cron: 미복약 감지 + 알림 발송."""
    await check_missed_medications()
