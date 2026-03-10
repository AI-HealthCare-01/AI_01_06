from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, guides, medications, prescriptions, users
from app.core.database import close_db, init_db
from app.core.redis import close_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_redis_pool()
    await close_db()


app = FastAPI(title="Project & Sullivan API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(prescriptions.router)
app.include_router(medications.router)
app.include_router(guides.router)
app.include_router(chat.router)


@app.get("/api/health")
async def health_check():
    return {"success": True, "data": {"status": "ok"}, "error": None}
