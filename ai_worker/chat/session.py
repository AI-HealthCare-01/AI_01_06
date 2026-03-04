from redis.asyncio import Redis

from ai_worker.schemas.chat import ChatMessage


class RedisSessionManager:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.ttl = 3600

    def _get_key(self, session_id: str) -> str:
        return f"chat:session:{session_id}"

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        key = self._get_key(session_id)
        messages_json = await self.redis.lrange(key, 0, -1)
        return [ChatMessage.model_validate_json(msg) for msg in messages_json]

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        key = self._get_key(session_id)
        msg = ChatMessage(role=role, content=content)
        await self.redis.rpush(key, msg.model_dump_json())
        await self.redis.expire(key, self.ttl)

    async def clear(self, session_id: str) -> None:
        key = self._get_key(session_id)
        await self.redis.delete(key)
