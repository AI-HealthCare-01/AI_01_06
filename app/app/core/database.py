from app import config

TORTOISE_ORM = {
    "connections": {"default": config.DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.auth_provider",
                "app.models.terms_consent",
                "app.models.patient_profile",
                "app.models.caregiver_patient",
                "app.models.prescription",
                "app.models.schedule",
                "app.models.notification",
                "app.models.audit",
                "app.models.guide",
                "app.models.chat",
                "app.models.drug_document",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
