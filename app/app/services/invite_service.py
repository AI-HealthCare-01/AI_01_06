import secrets

from app.core.redis import get_state_redis

INVITE_TOKEN_TTL = 48 * 60 * 60  # 48시간
_INVITE_PREFIX = "invite:"
_USER_INVITE_PREFIX = "invite_user:"  # 사용자당 현재 활성 토큰 추적


async def create_invite_token(user_id: int, user_role: str) -> str:
    """초대 토큰을 생성하고 Redis에 저장한다. 48시간 TTL.

    재발급 시 기존 활성 토큰을 무효화하여 Redis 키 누적을 방지한다.
    """
    redis = await get_state_redis()
    user_key = f"{_USER_INVITE_PREFIX}{user_id}"

    # 기존 활성 토큰 무효화
    old_token = await redis.get(user_key)
    if old_token:
        await redis.delete(f"{_INVITE_PREFIX}{old_token}")

    token = secrets.token_urlsafe(32)
    await redis.setex(f"{_INVITE_PREFIX}{token}", INVITE_TOKEN_TTL, f"{user_id}:{user_role}")
    await redis.setex(user_key, INVITE_TOKEN_TTL, token)
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
    # 토큰 데이터로 user_id를 찾아 user 추적 키도 함께 정리
    data = await redis.get(f"{_INVITE_PREFIX}{token}")
    if data:
        user_id_str = data.split(":")[0]
        await redis.delete(f"{_USER_INVITE_PREFIX}{user_id_str}")
    deleted = await redis.delete(f"{_INVITE_PREFIX}{token}")
    return deleted > 0
