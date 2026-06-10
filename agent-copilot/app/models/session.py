from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CopilotMessage:
    role: str
    content: str
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CopilotCheckpoint:
    checkpoint_id: str
    parent_checkpoint_id: Optional[str]
    step: Optional[str] = None
    messages: List[CopilotMessage] = field(default_factory=list)
    draft_profile: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    pending_action: Optional[Dict[str, Any]] = None
    agent_trace: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CopilotSession:
    session_id: str
    user_id: str
    messages: List[CopilotMessage] = field(default_factory=list)
    checkpoints: List[CopilotCheckpoint] = field(default_factory=list)
    current_step: str = "created"
    current_draft: Optional[Dict[str, Any]] = None
    pending_action: Optional[Dict[str, Any]] = None
    last_validation_result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def touch(self) -> None:
        self.updated_at = utc_now_iso()
