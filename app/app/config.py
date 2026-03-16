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

RAG_ENABLED: bool = os.environ.get("RAG_ENABLED", "false").lower() == "true"
RAG_MAX_CONTEXT_CHARS: int = int(os.environ.get("RAG_MAX_CONTEXT_CHARS", "2000"))
RAG_DEFAULT_SECTIONS: list[str] = ["dosage", "precautions"]
RAG_FAISS_TOP_K: int = int(os.environ.get("RAG_FAISS_TOP_K", "50"))
RAG_SIMILARITY_THRESHOLD: float = float(os.environ.get("RAG_SIMILARITY_THRESHOLD", "0.2"))
EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

EAYAK_API_KEY: str = os.environ.get("EAYAK_API_KEY", "")

KAKAO_CLIENT_ID: str = os.environ.get("KAKAO_CLIENT_ID", "")
KAKAO_CLIENT_SECRET: str = os.environ.get("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI: str = os.environ.get("KAKAO_REDIRECT_URI", "http://localhost:3000/auth/kakao/callback")

GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI: str = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
