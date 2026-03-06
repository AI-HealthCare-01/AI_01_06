import os

REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")

DATABASE_URL: str = os.environ.get("DATABASE_URL", "mysql://root:password@localhost:3306/sullivan")

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

NAVER_OCR_SECRET: str = os.environ.get("NAVER_OCR_SECRET", "")
NAVER_OCR_URL: str = os.environ.get("NAVER_OCR_URL", "")
