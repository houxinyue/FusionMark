from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Dict

from app.models.session import CopilotSession


class CopilotSessionStore(ABC):
    @abstractmethod
    def create(self, user_id: str) -> CopilotSession:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> CopilotSession:
        raise NotImplementedError

    @abstractmethod
    def save(self, session: CopilotSession) -> None:
        raise NotImplementedError


class InMemoryCopilotSessionStore(CopilotSessionStore):
    def __init__(self) -> None:
        self._sessions: Dict[str, CopilotSession] = {}

    def create(self, user_id: str) -> CopilotSession:
        session = CopilotSession(session_id=uuid.uuid4().hex, user_id=user_id)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> CopilotSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise KeyError(f"Copilot session '{session_id}' not found") from exc

    def save(self, session: CopilotSession) -> None:
        session.touch()
        self._sessions[session.session_id] = session
