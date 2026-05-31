from __future__ import annotations

import io
import json
from typing import Any, Dict

from app.storage.archive_store import ArchiveStore


class MinioArchiveStore(ArchiveStore):
    """MinIO archive store for long-term session replay payloads."""

    def __init__(
        self,
        client: Any,
        bucket: str,
        prefix: str = "fusion-mark",
        project: str = "fusion-mark",
        env: str = "dev",
    ) -> None:
        self._client = client
        self._bucket = bucket
        self._prefix = prefix.strip("/")
        self._project = project
        self._env = env

    @classmethod
    def from_endpoint(
        cls,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        *,
        secure: bool = False,
        prefix: str = "fusion-mark",
        project: str = "fusion-mark",
        env: str = "dev",
    ) -> "MinioArchiveStore":
        try:
            from minio import Minio
        except ImportError as exc:
            raise RuntimeError("Install minio to use MinioArchiveStore") from exc
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        return cls(client, bucket=bucket, prefix=prefix, project=project, env=env)

    def archive_session(self, session_id: str, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        stream = io.BytesIO(data)
        object_name = self._object_name(payload.get("user_id", "unknown"), session_id)
        self._client.put_object(
            self._bucket,
            object_name,
            stream,
            length=len(data),
            content_type="application/json",
        )

    def _object_name(self, user_id: str, session_id: str) -> str:
        parts = [
            self._prefix,
            self._project,
            self._env,
            "agent",
            str(user_id),
            "session",
            f"{session_id}.json",
        ]
        return "/".join(part for part in parts if part)
