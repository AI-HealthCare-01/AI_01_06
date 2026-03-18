from slowapi import Limiter
from starlette.requests import Request

from app import config


def _get_client_ip(request: Request) -> str:
    """Nginx가 설정한 X-Real-IP 헤더에서 클라이언트 IP를 추출.

    X-Forwarded-For는 클라이언트가 직접 조작할 수 있어 스푸핑 위험이 있으므로,
    Nginx가 $remote_addr로 설정하는 X-Real-IP를 우선 사용한다.
    """
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_client_ip, storage_uri=config.REDIS_URL)
