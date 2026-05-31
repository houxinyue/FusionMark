from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ArchiveStore(ABC):
    @abstractmethod
    def archive_session(self, session_id: str, payload: Dict[str, Any]) -> None:
        raise NotImplementedError


class NoopArchiveStore(ArchiveStore):
    def archive_session(self, session_id: str, payload: Dict[str, Any]) -> None:
        return None
