from app.models.session import CopilotCheckpoint, CopilotMessage, CopilotSession
from app.storage.serialization import (
    archive_payload,
    checkpoint_from_dict,
    checkpoint_to_dict,
    message_from_dict,
    message_to_dict,
    session_from_dict,
    session_to_dict,
)


def test_session_serialization_round_trip() -> None:
    session = CopilotSession(
        session_id="s1",
        user_id="u1",
        current_step="reviewing_draft",
        current_draft={"name": "paper"},
        pending_action={"action": "save_profile"},
        last_validation_result={"valid": True, "errors": []},
    )
    session.messages.append(
        CopilotMessage(
            role="user",
            content="hello",
            message_type="text",
            metadata={"source": "chat"},
        )
    )
    session.checkpoints.append(
        CopilotCheckpoint(
            checkpoint_id="c1",
            parent_checkpoint_id=None,
            step="reviewing_draft",
            messages=list(session.messages),
            draft_profile={"name": "paper"},
            validation_result={"valid": True, "errors": []},
            pending_action={"action": "save_profile"},
            agent_trace={"intent": "create_profile", "node": "draft_generator"},
        )
    )

    serialized = session_to_dict(session)
    restored = session_from_dict(serialized)

    assert serialized["schema_version"] == "1.1"
    assert restored.session_id == "s1"
    assert restored.user_id == "u1"
    assert restored.messages[0].content == "hello"
    assert restored.messages[0].metadata == {"source": "chat"}
    assert restored.checkpoints[0].checkpoint_id == "c1"
    assert restored.checkpoints[0].step == "reviewing_draft"
    assert restored.current_draft == {"name": "paper"}
    assert restored.pending_action == {"action": "save_profile"}
    assert restored.last_validation_result == {"valid": True, "errors": []}


def test_message_serialization_preserves_metadata() -> None:
    message = CopilotMessage(
        role="assistant",
        content="ready",
        message_type="draft_summary",
        metadata={"draft_id": "d1"},
    )

    restored = message_from_dict(message_to_dict(message))

    assert restored.message_type == "draft_summary"
    assert restored.metadata == {"draft_id": "d1"}


def test_checkpoint_serialization_preserves_enriched_snapshot() -> None:
    checkpoint = CopilotCheckpoint(
        checkpoint_id="c1",
        parent_checkpoint_id="c0",
        step="validating_profile",
        draft_profile={"name": "paper"},
        validation_result={"valid": False},
        pending_action={"action": "save_profile"},
        agent_trace={"intent": "repair_profile"},
    )

    restored = checkpoint_from_dict(checkpoint_to_dict(checkpoint))

    assert restored.step == "validating_profile"
    assert restored.draft_profile == {"name": "paper"}
    assert restored.validation_result == {"valid": False}
    assert restored.pending_action == {"action": "save_profile"}
    assert restored.agent_trace == {"intent": "repair_profile"}


def test_legacy_session_payload_defaults_new_fields() -> None:
    legacy_session = {
        "schema_version": "1.0",
        "session_id": "s1",
        "user_id": "u1",
        "messages": [
            {
                "role": "user",
                "content": "hello",
                "created_at": "2026-06-10T00:00:00+00:00",
            }
        ],
        "checkpoints": [
            {
                "checkpoint_id": "c1",
                "parent_checkpoint_id": None,
                "messages": [],
                "created_at": "2026-06-10T00:01:00+00:00",
            }
        ],
        "current_step": "created",
        "created_at": "2026-06-10T00:00:00+00:00",
        "updated_at": "2026-06-10T00:02:00+00:00",
    }

    restored = session_from_dict(legacy_session)

    assert restored.current_draft is None
    assert restored.pending_action is None
    assert restored.last_validation_result is None
    assert restored.messages[0].message_type == "text"
    assert restored.messages[0].metadata is None
    assert restored.checkpoints[0].step is None
    assert restored.checkpoints[0].draft_profile is None


def test_archive_payload_contains_replay_fields_and_summary() -> None:
    session = CopilotSession(
        session_id="s1",
        user_id="u1",
        current_step="reviewing_draft",
        current_draft={"name": "paper"},
        pending_action={"action": "save_profile"},
        last_validation_result={"valid": True},
    )
    checkpoint = CopilotCheckpoint(
        checkpoint_id="c1",
        parent_checkpoint_id=None,
        step="reviewing_draft",
        draft_profile={"name": "paper"},
        validation_result={"valid": True},
        pending_action={"action": "save_profile"},
        agent_trace={"node": "draft_generator"},
    )

    payload = archive_payload(session, [checkpoint], project="fusion-mark", env="test")

    assert payload["schema_version"] == "1.1"
    assert payload["project"] == "fusion-mark"
    assert payload["env"] == "test"
    assert payload["current_draft"] == {"name": "paper"}
    assert payload["pending_action"] == {"action": "save_profile"}
    assert payload["last_validation_result"] == {"valid": True}
    assert payload["checkpoints"][0]["step"] == "reviewing_draft"
    assert payload["checkpoints"][0]["agent_trace"] == {"node": "draft_generator"}
    assert payload["summary"]["checkpoint_count"] == 1
