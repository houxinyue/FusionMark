from __future__ import annotations

from app.storage.message_store import MessageStore
from app.storage.session_store import CopilotSessionStore


class CopilotCoreService:
    def __init__(self, session_store: CopilotSessionStore) -> None:
        self.session_store = session_store
        self.message_store = MessageStore(session_store)
