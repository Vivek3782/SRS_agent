import json
import redis
from app.config import settings


class RedisService:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True  # return strings, not bytes
        )

    def get_session(self, session_id: str) -> dict | None:
        key = f"session:{session_id}"
        value = self.client.get(key)

        if not value:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # corrupted data → treat as new session
            return None

    def set_session(self, session_id: str, data: dict) -> None:
        key = f"session:{session_id}"
        self.client.setex(
            key,
            settings.redis_ttl_seconds,
            json.dumps(data)
        )

    def delete_session(self, session_id: str) -> None:
        key = f"session:{session_id}"
        self.client.delete(key)


redis_service = RedisService()
