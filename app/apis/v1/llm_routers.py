import httpx

from fastapi import APIRouter, HTTPException

from app.core import config

llm_router = APIRouter(prefix="/llm", tags=["LLM"])


@llm_router.get("/ping")
async def llm_ping():
    """ai_worker의 /llm/ping 엔드포인트로 요청을 프록시합니다."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{config.AI_WORKER_BASE_URL}/llm/ping")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text) from e
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"ai_worker unreachable: {e}") from e
