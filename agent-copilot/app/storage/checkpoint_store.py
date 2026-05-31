from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from app.models.session import CopilotCheckpoint


class CheckpointStore(ABC):
    @abstractmethod
    def save(self, session_id: str, checkpoint: CopilotCheckpoint) -> None:
        raise NotImplementedError

    @abstractmethod
    def list(self, session_id: str) -> List[CopilotCheckpoint]:
        raise NotImplementedError


class InMemoryCheckpointStore(CheckpointStore):
    def __init__(self) -> None:
        self._checkpoints: Dict[str, List[CopilotCheckpoint]] = {}

    def save(self, session_id: str, checkpoint: CopilotCheckpoint) -> None:
        self._checkpoints.setdefault(session_id, []).append(checkpoint)

    def list(self, session_id: str) -> List[CopilotCheckpoint]:
        return list(self._checkpoints.get(session_id, []))
