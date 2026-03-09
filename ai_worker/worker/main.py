from arq.connections import RedisSettings
from tortoise import Tortoise

from worker import config
from worker.tasks.guide_task import guide_task
from worker.tasks.ocr_task import ocr_task

TORTOISE_ORM = {
    "db_url": config.DATABASE_URL,
    "modules": {"models": [
        "app.models.user", "app.models.prescription", "app.models.guide", "app.models.chat",
    ]},
}


async def startup(ctx: dict) -> None:
    await Tortoise.init(**TORTOISE_ORM)


async def shutdown(ctx: dict) -> None:
    await Tortoise.close_connections()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    functions = [ocr_task, guide_task]
    on_startup = startup
    on_shutdown = shutdown
