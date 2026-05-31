from __future__ import annotations

from dataclasses import dataclass

from app.storage.archive_store import NoopArchiveStore
from app.storage.checkpoint_store import InMemoryCheckpointStore
from app.storage.persistence import CopilotPersistenceBoundary, PersistenceContext
from app.storage.session_store import InMemoryCopilotSessionStore


@dataclass(frozen=True)
class PersistenceSettings:
    project: str = "fusion-mark"
    env: str = "dev"


def create_in_memory_persistence(settings: PersistenceSettings | None = None) -> CopilotPersistenceBoundary:
    settings = settings or PersistenceSettings()
    return CopilotPersistenceBoundary(
        session_store=InMemoryCopilotSessionStore(),
        checkpoint_store=InMemoryCheckpointStore(),
        archive_store=NoopArchiveStore(),
        context=PersistenceContext(project=settings.project, env=settings.env),
    )
