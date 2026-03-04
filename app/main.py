from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.apis.v1 import v1_routers
from app.core import config
from app.db.databases import initialize_tortoise

app = FastAPI(
    title="AI Healthcare API",
    version="1.0.0",
    description="AI Healthcare 프로젝트 백엔드 API (B담당: OCR 파이프라인 + 약 데이터)",
    default_response_class=ORJSONResponse,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

initialize_tortoise(app)

# ── B담당: 업로드 디렉토리 자동 생성 + 정적 파일 서빙 ──────────────────────────
_upload_root = Path(config.UPLOAD_DIR)
_upload_root.mkdir(parents=True, exist_ok=True)

app.mount(
    config.STATIC_URL_PREFIX,  # "/static"
    StaticFiles(directory=config.UPLOAD_DIR),
    name="static",
)

app.include_router(v1_routers)
