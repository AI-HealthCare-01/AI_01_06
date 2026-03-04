import os
import uuid
import zoneinfo
from dataclasses import field
from enum import StrEnum
from pathlib import Path

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
    DB_PASSWORD: str = "pw1234"
    DB_NAME: str = "ai_health"
    DB_CONNECT_TIMEOUT: int = 5
    DB_CONNECTION_POOL_MAXSIZE: int = 10

    COOKIE_DOMAIN: str = "localhost"

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 14 * 24 * 60
    JWT_LEEWAY: int = 5

    # ── B담당: CLOVA OCR ──────────────────────────────────────────────
    CLOVA_OCR_API_URL: str = "https://CHANGE_ME.apigw.ntruss.com/custom/v1/00000/general"
    CLOVA_OCR_SECRET_KEY: str = "CHANGE_ME_CLOVA_SECRET"

    # B담당: OpenAI (structured parsing 용)
    OPENAI_API_KEY: str = "CHANGE_ME_OPENAI_KEY"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # B담당: 파일 업로드
    UPLOAD_DIR: str = "./uploads"
    STATIC_URL_PREFIX: str = "/static"
    MAX_UPLOAD_SIZE_MB: int = 10

    # B담당: OCR 실행 모드 ("real" | "mock")  — 키 없을 때 mock으로 테스트 가능
    OCR_MODE: str = "mock"
