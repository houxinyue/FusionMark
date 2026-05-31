from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CopilotMessage:
    role: str
    content: str
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CopilotCheckpoint:
    checkpoint_id: str
    parent_checkpoint_id: Optional[str]
    messages: List[CopilotMessage] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CopilotSession:
    session_id: str
    user_id: str
    messages: List[CopilotMessage] = field(default_factory=list)
    checkpoints: List[CopilotCheckpoint] = field(default_factory=list)
    current_step: str = "created"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def touch(self) -> None:
        self.updated_at = utc_now_iso()
