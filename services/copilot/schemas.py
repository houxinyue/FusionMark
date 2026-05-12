"""Data transfer objects for the Profile Config Copilot."""

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
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CopilotValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    config: Optional[Dict[str, Any]] = None


@dataclass
class CopilotReferencedProfile:
    profile_id: str
    display_name: str
    description: Optional[str] = None
    score: int = 0
    summary: str = ""


@dataclass
class CopilotSession:
    session_id: str
    user_id: str
    messages: List[CopilotMessage] = field(default_factory=list)
    current_draft_yaml: str = ""
    validation: CopilotValidationResult = field(default_factory=lambda: CopilotValidationResult(valid=False))
    referenced_profiles: List[CopilotReferencedProfile] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def touch(self) -> None:
        self.updated_at = utc_now_iso()


@dataclass
class DraftGenerationRequest:
    user_message: str
    current_draft_yaml: str = ""
    conversation: List[CopilotMessage] = field(default_factory=list)
    referenced_profiles: List[CopilotReferencedProfile] = field(default_factory=list)


@dataclass
class DraftGenerationResult:
    assistant_message: str
    draft_yaml: str
