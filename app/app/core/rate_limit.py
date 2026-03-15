from slowapi import Limiter
from starlette.requests import Request

from app import config


def _get_client_ip(request: Request) -> str:
    """X-Forwarded-For 헤더에서 클라이언트 IP를 추출. Nginx 프록시 뒤에서도 정확한 IP 반환."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_client_ip, storage_uri=config.REDIS_URL)
