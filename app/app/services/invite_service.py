import secrets

from app.core.redis import get_state_redis

INVITE_TOKEN_TTL = 48 * 60 * 60  # 48시간
_INVITE_PREFIX = "invite:"


async def create_invite_token(user_id: int, user_role: str) -> str:
    """초대 토큰을 생성하고 Redis에 저장한다. 48시간 TTL."""
    token = secrets.token_urlsafe(32)
    redis = await get_state_redis()
    await redis.setex(f"{_INVITE_PREFIX}{token}", INVITE_TOKEN_TTL, f"{user_id}:{user_role}")
    return token


async def get_invite_data(token: str) -> dict | None:
    """토큰으로 초대자 정보를 조회한다. 만료/미존재 시 None."""
    redis = await get_state_redis()
    data = await redis.get(f"{_INVITE_PREFIX}{token}")
    if not data:
        return None
    user_id_str, user_role = data.split(":")
    return {"user_id": int(user_id_str), "role": user_role}


async def consume_invite_token(token: str) -> bool:
    """토큰을 소비(삭제)한다. 성공 시 True."""
    redis = await get_state_redis()
    deleted = await redis.delete(f"{_INVITE_PREFIX}{token}")
    return deleted > 0
