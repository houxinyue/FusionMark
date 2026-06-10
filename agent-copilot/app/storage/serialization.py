from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional

from app.models.session import CopilotCheckpoint, CopilotMessage, CopilotSession


SCHEMA_VERSION = "1.1"


def message_to_dict(message: CopilotMessage) -> Dict[str, Any]:
    return asdict(message)


def message_from_dict(data: Dict[str, Any]) -> CopilotMessage:
    return CopilotMessage(
        role=str(data["role"]),
        content=str(data["content"]),
        message_type=str(data.get("message_type", "text")),
        metadata=_optional_dict(data.get("metadata")),
        created_at=str(data["created_at"]),
    )


def checkpoint_to_dict(checkpoint: CopilotCheckpoint) -> Dict[str, Any]:
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "parent_checkpoint_id": checkpoint.parent_checkpoint_id,
        "step": checkpoint.step,
        "messages": [message_to_dict(message) for message in checkpoint.messages],
        "draft_profile": checkpoint.draft_profile,
        "validation_result": checkpoint.validation_result,
        "pending_action": checkpoint.pending_action,
        "agent_trace": checkpoint.agent_trace,
        "created_at": checkpoint.created_at,
    }


def checkpoint_from_dict(data: Dict[str, Any]) -> CopilotCheckpoint:
    return CopilotCheckpoint(
        checkpoint_id=str(data["checkpoint_id"]),
        parent_checkpoint_id=_optional_str(data.get("parent_checkpoint_id")),
        step=_optional_str(data.get("step")),
        messages=[message_from_dict(message) for message in data.get("messages", [])],
        draft_profile=_optional_dict(data.get("draft_profile")),
        validation_result=_optional_dict(data.get("validation_result")),
        pending_action=_optional_dict(data.get("pending_action")),
        agent_trace=_optional_dict(data.get("agent_trace")),
        created_at=str(data["created_at"]),
    )


def session_to_dict(session: CopilotSession) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session.session_id,
        "user_id": session.user_id,
        "messages": [message_to_dict(message) for message in session.messages],
        "checkpoints": [checkpoint_to_dict(checkpoint) for checkpoint in session.checkpoints],
        "current_step": session.current_step,
        "current_draft": session.current_draft,
        "pending_action": session.pending_action,
        "last_validation_result": session.last_validation_result,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def session_from_dict(data: Dict[str, Any]) -> CopilotSession:
    return CopilotSession(
        session_id=str(data["session_id"]),
        user_id=str(data["user_id"]),
        messages=[message_from_dict(message) for message in data.get("messages", [])],
        checkpoints=[checkpoint_from_dict(checkpoint) for checkpoint in data.get("checkpoints", [])],
        current_step=str(data.get("current_step", "created")),
        current_draft=_optional_dict(data.get("current_draft")),
        pending_action=_optional_dict(data.get("pending_action")),
        last_validation_result=_optional_dict(data.get("last_validation_result")),
        created_at=str(data["created_at"]),
        updated_at=str(data["updated_at"]),
    )


def archive_payload(
    session: CopilotSession,
    checkpoints: Iterable[CopilotCheckpoint],
    *,
    project: str,
    env: str,
) -> Dict[str, Any]:
    checkpoint_list = list(checkpoints)
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "env": env,
        "user_id": session.user_id,
        "session_id": session.session_id,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": [message_to_dict(message) for message in session.messages],
        "checkpoints": [checkpoint_to_dict(checkpoint) for checkpoint in checkpoint_list],
        "current_step": session.current_step,
        "current_draft": session.current_draft,
        "pending_action": session.pending_action,
        "last_validation_result": session.last_validation_result,
        "summary": {
            "message_count": len(session.messages),
            "checkpoint_count": len(checkpoint_list),
        },
    }


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _optional_dict(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    raise TypeError(f"Expected dict or None, got {type(value).__name__}")
