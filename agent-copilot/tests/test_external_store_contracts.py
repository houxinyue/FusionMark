import json

from app.models.session import CopilotCheckpoint, CopilotMessage, CopilotSession
from app.storage.minio_archive import MinioArchiveStore
from app.storage.redis_store import RedisCheckpointStore, RedisCopilotSessionStore


class FakeRedisClient:
    def __init__(self) -> None:
        self.strings = {}
        self.sorted_sets = {}
        self.expirations = {}

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.strings[key] = value
        self.expirations[key] = ttl_seconds

    def get(self, key: str) -> str | None:
        return self.strings.get(key)

    def zadd(self, key: str, values: dict[str, int]) -> None:
        self.sorted_sets.setdefault(key, {}).update(values)

    def zrange(self, key: str, start: int, end: int) -> list[str]:
        items = sorted(self.sorted_sets.get(key, {}).items(), key=lambda item: item[1])
        values = [item[0] for item in items]
        if end == -1:
            return values[start:]
        return values[start : end + 1]

    def expire(self, key: str, ttl_seconds: int) -> None:
        self.expirations[key] = ttl_seconds


class FakeMinioClient:
    def __init__(self) -> None:
        self.objects = []

    def put_object(
        self,
        bucket: str,
        object_name: str,
        stream,
        *,
        length: int,
        content_type: str,
    ) -> None:
        self.objects.append(
            {
                "bucket": bucket,
                "object_name": object_name,
                "payload": json.loads(stream.read().decode("utf-8")),
                "length": length,
                "content_type": content_type,
            }
        )


def test_redis_session_store_preserves_key_pattern_and_enriched_state() -> None:
    client = FakeRedisClient()
    store = RedisCopilotSessionStore(client)
    session = CopilotSession(
        session_id="s1",
        user_id="u1",
        current_step="reviewing_draft",
        current_draft={"name": "paper"},
        pending_action={"action": "save_profile"},
        last_validation_result={"valid": True},
    )
    session.messages.append(
        CopilotMessage(role="assistant", content="ready", metadata={"source": "test"})
    )

    store.save(session)
    restored = store.get("s1")

    assert "agent-copilot:session:s1" in client.strings
    assert restored.current_draft == {"name": "paper"}
    assert restored.pending_action == {"action": "save_profile"}
    assert restored.last_validation_result == {"valid": True}
    assert restored.messages[0].metadata == {"source": "test"}


def test_redis_checkpoint_store_preserves_key_pattern_and_enriched_state() -> None:
    client = FakeRedisClient()
    store = RedisCheckpointStore(client)
    checkpoint = CopilotCheckpoint(
        checkpoint_id="c1",
        parent_checkpoint_id=None,
        step="validating_profile",
        draft_profile={"name": "paper"},
        validation_result={"valid": False},
        pending_action={"action": "save_profile"},
        agent_trace={"node": "validator"},
    )

    store.save("s1", checkpoint)
    restored = store.list("s1")

    assert "agent-copilot:session:s1:checkpoints" in client.sorted_sets
    assert restored[0].step == "validating_profile"
    assert restored[0].draft_profile == {"name": "paper"}
    assert restored[0].validation_result == {"valid": False}
    assert restored[0].pending_action == {"action": "save_profile"}
    assert restored[0].agent_trace == {"node": "validator"}


def test_minio_archive_store_preserves_object_path() -> None:
    client = FakeMinioClient()
    store = MinioArchiveStore(
        client,
        bucket="fusion-mark",
        prefix="fusion-mark",
        project="fusion-mark",
        env="test",
    )
    payload = {
        "user_id": "u1",
        "session_id": "s1",
        "current_draft": {"name": "paper"},
    }

    store.archive_session("s1", payload)

    assert client.objects[0]["bucket"] == "fusion-mark"
    assert (
        client.objects[0]["object_name"]
        == "fusion-mark/fusion-mark/test/agent/u1/session/s1.json"
    )
    assert client.objects[0]["payload"]["current_draft"] == {"name": "paper"}
