from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict

from app.models.session import CopilotCheckpoint, CopilotSession
from app.storage.archive_store import ArchiveStore
from app.storage.checkpoint_store import CheckpointStore
from app.storage.message_store import MessageStore
from app.storage.serialization import archive_payload
from app.storage.session_store import CopilotSessionStore


@dataclass(frozen=True)
class PersistenceContext:
    project: str = "fusion-mark"
    env: str = "dev"


class CopilotPersistenceBoundary:
    """Single boundary for session runtime state and long-term archives."""

    def __init__(
        self,
        session_store: CopilotSessionStore,
        checkpoint_store: CheckpointStore,
        archive_store: ArchiveStore,
        context: PersistenceContext | None = None,
    ) -> None:
        self.session_store = session_store
        self.checkpoint_store = checkpoint_store
        self.archive_store = archive_store
        self.context = context or PersistenceContext()
        self.messages = MessageStore(session_store)

    def create_session(self, user_id: str) -> CopilotSession:
        return self.session_store.create(user_id)

    def get_session(self, session_id: str) -> CopilotSession:
        return self.session_store.get(session_id)

    def save_session(self, session: CopilotSession) -> None:
        self.session_store.save(session)

    def create_checkpoint(self, session_id: str) -> CopilotCheckpoint:
        session = self.session_store.get(session_id)
        checkpoints = self.checkpoint_store.list(session_id)
        parent_checkpoint_id = checkpoints[-1].checkpoint_id if checkpoints else None
        checkpoint = CopilotCheckpoint(
            checkpoint_id=uuid.uuid4().hex,
            parent_checkpoint_id=parent_checkpoint_id,
            step=session.current_step,
            messages=list(session.messages),
            draft_profile=session.current_draft,
            validation_result=session.last_validation_result,
            pending_action=session.pending_action,
        )
        session.checkpoints.append(checkpoint)
        self.session_store.save(session)
        self.checkpoint_store.save(session_id, checkpoint)
        return checkpoint

    def archive_session(self, session_id: str) -> Dict[str, Any]:
        session = self.session_store.get(session_id)
        checkpoints = self.checkpoint_store.list(session_id)
        payload = archive_payload(
            session,
            checkpoints,
            project=self.context.project,
            env=self.context.env,
        )
        self.archive_store.archive_session(session_id, payload)
        return payload
