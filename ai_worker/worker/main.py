from datetime import timedelta, timezone

from arq.connections import RedisSettings
from arq.cron import cron
from tortoise import Tortoise

from worker import config
from worker.tasks.chat_task import chat_task
from worker.tasks.guide_task import guide_task
from worker.tasks.medication_check_task import medication_check_cron
from worker.tasks.ocr_task import ocr_task
from worker.tasks.purge_task import purge_deleted_users

KST = timezone(timedelta(hours=9))

TORTOISE_ORM = {
    "db_url": config.DATABASE_URL,
    "modules": {
        "models": [
            "app.models.user",
            "app.models.prescription",
            "app.models.guide",
            "app.models.chat",
            "app.models.patient_profile",
            "app.models.auth_provider",
            "app.models.terms_consent",
            "app.models.audit",
            "app.models.notification",
            "app.models.caregiver_patient",
            "app.models.schedule",
        ]
    },
}


async def startup(ctx: dict) -> None:
    await Tortoise.init(**TORTOISE_ORM)


async def shutdown(ctx: dict) -> None:
    await Tortoise.close_connections()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    functions = [ocr_task, guide_task, chat_task]
    cron_jobs = [
        cron(purge_deleted_users, hour=4, minute=0),
        cron(medication_check_cron, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
    ]
    timezone = KST
    on_startup = startup
    on_shutdown = shutdown
