from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.redis import get_state_redis
from app.core.security import decode_token
from app.models.user import User

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    # jti가 있으면 blacklist 확인 (기존 jti 없는 토큰은 skip → 하위 호환)
    jti = payload.get("jti")
    if jti:
        redis = await get_state_redis()
        if await redis.get(f"blacklist:{jti}"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그아웃된 토큰입니다.")
    user_id = int(payload["sub"])
    user = await User.get_or_none(id=user_id, deleted_at__isnull=True)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
