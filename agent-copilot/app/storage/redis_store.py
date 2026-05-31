from __future__ import annotations

import json
import uuid
from typing import Any, List

from app.models.session import CopilotCheckpoint, CopilotSession
from app.storage.checkpoint_store import CheckpointStore
from app.storage.serialization import checkpoint_from_dict, checkpoint_to_dict, session_from_dict, session_to_dict
from app.storage.session_store import CopilotSessionStore


class RedisCopilotSessionStore(CopilotSessionStore):
    """Redis-backed session store using JSON payloads at the persistence boundary."""

    def __init__(self, client: Any, key_prefix: str = "agent-copilot", ttl_seconds: int = 864000) -> None:
        self._client = client
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    @classmethod
    def from_url(cls, redis_url: str, key_prefix: str = "agent-copilot", ttl_seconds: int = 864000) -> "RedisCopilotSessionStore":
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use RedisCopilotSessionStore") from exc
        return cls(redis.Redis.from_url(redis_url, decode_responses=True), key_prefix, ttl_seconds)

    def create(self, user_id: str) -> CopilotSession:
        session = CopilotSession(session_id=uuid.uuid4().hex, user_id=user_id)
        self.save(session)
        return session

    def get(self, session_id: str) -> CopilotSession:
        raw = self._client.get(self._session_key(session_id))
        if raw is None:
            raise KeyError(f"Copilot session '{session_id}' not found")
        return session_from_dict(json.loads(raw))

    def save(self, session: CopilotSession) -> None:
        session.touch()
        self._client.setex(self._session_key(session.session_id), self._ttl_seconds, json.dumps(session_to_dict(session), ensure_ascii=False))

    def _session_key(self, session_id: str) -> str:
        return f"{self._key_prefix}:session:{session_id}"


class RedisCheckpointStore(CheckpointStore):
    """Redis-backed checkpoint store using a sorted list of JSON checkpoint payloads."""

    def __init__(self, client: Any, key_prefix: str = "agent-copilot", ttl_seconds: int = 864000) -> None:
        self._client = client
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    @classmethod
    def from_url(cls, redis_url: str, key_prefix: str = "agent-copilot", ttl_seconds: int = 864000) -> "RedisCheckpointStore":
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use RedisCheckpointStore") from exc
        return cls(redis.Redis.from_url(redis_url, decode_responses=True), key_prefix, ttl_seconds)

    def save(self, session_id: str, checkpoint: CopilotCheckpoint) -> None:
        key = self._checkpoint_key(session_id)
        payload = json.dumps(checkpoint_to_dict(checkpoint), ensure_ascii=False)
        score = len(self.list(session_id)) + 1
        self._client.zadd(key, {payload: score})
        self._client.expire(key, self._ttl_seconds)

    def list(self, session_id: str) -> List[CopilotCheckpoint]:
        raw_items = self._client.zrange(self._checkpoint_key(session_id), 0, -1)
        return [checkpoint_from_dict(json.loads(raw_item)) for raw_item in raw_items]

    def _checkpoint_key(self, session_id: str) -> str:
        return f"{self._key_prefix}:session:{session_id}:checkpoints"
