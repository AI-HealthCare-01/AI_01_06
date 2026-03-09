from tortoise import Tortoise

from app import config

TORTOISE_ORM = {
    "connections": {"default": config.DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.auth_provider",
                "app.models.terms_consent",
                "app.models.prescription",
                "app.models.guide",
                "app.models.chat",
            ],
            "default_connection": "default",
        },
    },
}


async def init_db() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db() -> None:
    await Tortoise.close_connections()
