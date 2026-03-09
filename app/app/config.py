import os

from dotenv import load_dotenv

# dotenv will load the file locally; existing env vars (e.g., from Docker) take precedence
load_dotenv("infra/env/.local.env")

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite://db.sqlite3")
REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")
SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

NAVER_OCR_SECRET: str = os.environ.get("NAVER_OCR_SECRET", "")
NAVER_OCR_URL: str = os.environ.get("NAVER_OCR_URL", "")

CHAT_CONTEXT_MESSAGE_COUNT: int = int(os.environ.get("CHAT_CONTEXT_MESSAGE_COUNT", "3"))
CHAT_STREAMING_TIMEOUT_SECONDS: int = int(os.environ.get("CHAT_STREAMING_TIMEOUT_SECONDS", "60"))
