from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.apis.v1 import v1_routers
from app.apis.v1.llm_routers import llm_router
from app.db.databases import initialize_tortoise

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_tortoise(app)

app.include_router(v1_routers)
app.include_router(llm_router, prefix="/api/v1")
