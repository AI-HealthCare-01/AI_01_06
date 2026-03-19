import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.caregiver_patient import CaregiverPatientMapping
from app.models.notification import Notification, NotificationSetting
from app.models.schedule import AdherenceLog, MedicationSchedule
from app.models.user import User

logger = logging.getLogger(__name__)

_ALLOWED_TYPES = {"MEDICATION", "CAREGIVER"}

_TYPE_SETTING_MAP: dict[str, str] = {
    "MEDICATION": "medication_enabled",
    "CAREGIVER": "caregiver_enabled",
}


async def create_notification(
    user_id: int,
    notification_type: str,
    title: str,
    body: str | None = None,
) -> Notification | None:
    """알림을 생성한다. 해당 유형이 disabled면 None을 반환한다.

    DB 오류 시 None을 반환하며 주요 비즈니스 로직을 차단하지 않는다.

    Raises:
        ValueError: 허용되지 않은 notification_type인 경우
    """
    if notification_type not in _ALLOWED_TYPES:
        raise ValueError(f"허용되지 않은 알림 유형: {notification_type}")

    try:
        setting_field = _TYPE_SETTING_MAP.get(notification_type)
        if setting_field:
            setting = await NotificationSetting.get_or_none(user_id=user_id)
            if setting and not getattr(setting, setting_field):
                return None

        return await Notification.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
        )
    except Exception:
        logger.exception("알림 생성 실패: user_id=%d type=%s", user_id, notification_type)
        return None


KST = ZoneInfo("Asia/Seoul")

TIME_OF_DAY_LABEL: dict[str, str] = {
    "MORNING": "아침",
    "NOON": "점심",
    "EVENING": "저녁",
    "BEDTIME": "자기전",
}

TIME_OF_DAY_SETTING_FIELD: dict[str, str] = {
    "MORNING": "morning_time",
    "NOON": "noon_time",
    "EVENING": "evening_time",
    "BEDTIME": "bedtime_time",
}

DEFAULT_TIMES: dict[str, str] = {
    "MORNING": "08:00",
    "NOON": "12:00",
    "EVENING": "18:00",
    "BEDTIME": "22:00",
}


def _now_kst() -> datetime:
    """현재 KST 시각 반환. 테스트에서 mock 가능."""
    return datetime.now(KST)


def _get_deadline(setting: NotificationSetting | None, tod: str, today: datetime) -> datetime:
    """시간대(tod)에 대한 미복약 판정 deadline(설정 시각 + 30분)을 반환한다."""
    field_name = TIME_OF_DAY_SETTING_FIELD.get(tod)
    setting_time_str = None
    if setting and field_name:
        setting_time_str = getattr(setting, field_name, None)
    if not setting_time_str:
        setting_time_str = DEFAULT_TIMES.get(tod, "08:00")
    h, m = map(int, str(setting_time_str).split(":")[:2])
    return datetime(today.year, today.month, today.day, h, m, tzinfo=KST) + timedelta(minutes=30)


def _build_missed_notifications(
    user_id: int,
    user_name: str,
    tod: str,
    missed: list[MedicationSchedule],
    caregiver_ids: list[int],
    caregiver_settings_map: dict[int, NotificationSetting],
) -> list[Notification]:
    """한 사용자의 한 시간대에 대한 미복약 알림 객체 목록을 생성한다."""
    tag = f"missed:{tod}"
    label = TIME_OF_DAY_LABEL.get(tod, tod)

    if len(missed) == 1:
        med_name = missed[0].medication.name
        patient_title = f"{label}, {med_name} 미복용"
        caregiver_title = f"{user_name}님 {label}, {med_name} 미복용"
    else:
        patient_title = f"{label} 미복용"
        caregiver_title = f"{user_name}님 {label} 미복용"

    result: list[Notification] = [
        Notification(user_id=user_id, notification_type="MEDICATION", title=patient_title, body=tag)
    ]
    for cid in caregiver_ids:
        c_setting = caregiver_settings_map.get(cid)
        if c_setting and not c_setting.caregiver_enabled:
            continue
        result.append(Notification(user_id=cid, notification_type="CAREGIVER", title=caregiver_title, body=tag))
    return result


async def _load_batch_data(
    active_schedules: list[MedicationSchedule], today: date, today_dt: datetime
) -> tuple[
    set[int],
    dict[int, NotificationSetting],
    dict[int, list[int]],
    dict[int, NotificationSetting],
    dict[int, User],
    set[tuple[int, str]],
]:
    """미복약 감지에 필요한 모든 데이터를 배치로 조회한다."""
    user_ids = {s.medication.prescription.user_id for s in active_schedules}
    schedule_ids = [s.id for s in active_schedules]

    today_logs = await AdherenceLog.filter(schedule_id__in=schedule_ids, target_date=today)
    logged_schedule_ids = {log.schedule_id for log in today_logs}

    today_med_notifications = await Notification.filter(
        user_id__in=user_ids,
        notification_type="MEDICATION",
        created_at__gte=today_dt,
    )
    sent_tags: set[tuple[int, str]] = set()
    for n in today_med_notifications:
        if n.body and n.body.startswith("missed:"):
            sent_tags.add((n.user_id, n.body))

    settings_map: dict[int, NotificationSetting] = {
        s.user_id: s for s in await NotificationSetting.filter(user_id__in=user_ids)
    }

    caregiver_mappings = await CaregiverPatientMapping.filter(patient_id__in=user_ids, status="APPROVED")
    patient_caregivers: dict[int, list[int]] = {}
    for m in caregiver_mappings:
        patient_caregivers.setdefault(m.patient_id, []).append(m.caregiver_id)

    all_caregiver_ids = {cid for cids in patient_caregivers.values() for cid in cids}
    caregiver_settings_map: dict[int, NotificationSetting] = {}
    if all_caregiver_ids:
        for s in await NotificationSetting.filter(user_id__in=all_caregiver_ids):
            caregiver_settings_map[s.user_id] = s

    user_map: dict[int, User] = {u.id: u for u in await User.filter(id__in=user_ids)}

    return logged_schedule_ids, settings_map, patient_caregivers, caregiver_settings_map, user_map, sent_tags


async def check_missed_medications() -> None:
    """미복약 스케줄을 감지하고 알림을 생성한다.

    성능 최적화: 모든 조회를 배치로 수행 (N+1 제거).
    알림 메시지: 미복약 1개 → 약물명 포함, 2개+ → 시간대만.
    """
    now = _now_kst()
    today = now.date()
    today_dt = datetime(today.year, today.month, today.day, tzinfo=KST)

    active_schedules = await MedicationSchedule.filter(
        start_date__lte=today,
        end_date__gte=today,
    ).prefetch_related("medication__prescription__user")

    if not active_schedules:
        return

    logged_ids, settings_map, patient_caregivers, cg_settings, user_map, sent_tags = await _load_batch_data(
        active_schedules,
        today,
        today_dt,
    )

    # 사용자별·시간대별 스케줄 그룹핑
    user_schedules: dict[int, dict[str, list[MedicationSchedule]]] = {}
    for s in active_schedules:
        uid = s.medication.prescription.user_id
        user_schedules.setdefault(uid, {}).setdefault(s.time_of_day, []).append(s)

    notifications_to_create: list[Notification] = []

    for user_id, by_tod in user_schedules.items():
        setting = settings_map.get(user_id)
        if setting and not setting.medication_enabled:
            continue

        for tod, tod_schedules in by_tod.items():
            if now < _get_deadline(setting, tod, today_dt):
                continue
            missed = [s for s in tod_schedules if s.id not in logged_ids]
            if not missed or (user_id, f"missed:{tod}") in sent_tags:
                continue

            user_obj = user_map.get(user_id)
            notifications_to_create.extend(
                _build_missed_notifications(
                    user_id=user_id,
                    user_name=user_obj.name if user_obj else "",
                    tod=tod,
                    missed=missed,
                    caregiver_ids=patient_caregivers.get(user_id, []),
                    caregiver_settings_map=cg_settings,
                )
            )

    if notifications_to_create:
        await Notification.bulk_create(notifications_to_create)
