from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.models.session import CopilotMessage, CopilotSession
from app.storage.session_store import CopilotSessionStore


@dataclass
class StoredMessage:
    session_id: str
    message: CopilotMessage


class MessageStore:
    """Persist messages inside the session boundary."""

    def __init__(self, session_store: CopilotSessionStore) -> None:
        self._session_store = session_store

    def append(self, session_id: str, role: str, content: str) -> CopilotMessage:
        session = self._session_store.get(session_id)
        message = CopilotMessage(role=role, content=content)
        session.messages.append(message)
        self._session_store.save(session)
        return message

    def append_user_message(self, session_id: str, content: str) -> CopilotMessage:
        return self.append(session_id, "user", content)

    def append_assistant_message(self, session_id: str, content: str) -> CopilotMessage:
        return self.append(session_id, "assistant", content)

    def list(self, session_id: str) -> List[CopilotMessage]:
        session = self._session_store.get(session_id)
        return list(session.messages)

    def replace(self, session_id: str, messages: List[CopilotMessage]) -> CopilotSession:
        session = self._session_store.get(session_id)
        session.messages = list(messages)
        self._session_store.save(session)
        return session
