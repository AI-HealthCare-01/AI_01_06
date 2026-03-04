import os
import uuid
import zoneinfo
from dataclasses import field
from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    ENV: Env = Env.LOCAL
    SECRET_KEY: str = f"default-secret-key{uuid.uuid4().hex}"
    TIMEZONE: zoneinfo.ZoneInfo = field(default_factory=lambda: zoneinfo.ZoneInfo("Asia/Seoul"))
    TEMPLATE_DIR: str = os.path.join(Path(__file__).resolve().parent.parent, "templates")

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str
    DB_NAME: str = "ai_health"
    DB_CONNECT_TIMEOUT: int = 5
    DB_CONNECTION_POOL_MAXSIZE: int = 10

    COOKIE_DOMAIN: str = "localhost"

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 14 * 24 * 60
    JWT_LEEWAY: int = 5

    AI_WORKER_BASE_URL: str = Field(..., description="Base URL for the AI Worker service")

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        env = info.data.get("ENV")
        if env in (Env.DEV, Env.PROD) and "default-secret-key" in v:
            raise ValueError("SECRET_KEY must be explicitly set in DEV and PROD environments")
        return v
