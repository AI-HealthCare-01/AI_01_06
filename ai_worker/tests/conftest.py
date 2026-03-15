import pytest
from tortoise import Tortoise

TEST_DB_URL = "sqlite://:memory:"


@pytest.fixture(autouse=True)
async def setup_db():
    await Tortoise.init(
        db_url=TEST_DB_URL,
        modules={
            "models": [
                "app.models.user",
                "app.models.prescription",
                "app.models.guide",
                "app.models.patient_profile",
                "app.models.auth_provider",
                "app.models.terms_consent",
            ]
        },
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()
