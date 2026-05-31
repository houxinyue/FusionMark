from app.models.session import CopilotCheckpoint, CopilotMessage, CopilotSession
from app.storage.serialization import archive_payload, session_from_dict, session_to_dict


def test_session_serialization_round_trip() -> None:
    session = CopilotSession(session_id="s1", user_id="u1")
    session.messages.append(CopilotMessage(role="user", content="hello"))
    session.checkpoints.append(
        CopilotCheckpoint(
            checkpoint_id="c1",
            parent_checkpoint_id=None,
            messages=list(session.messages),
        )
    )

    restored = session_from_dict(session_to_dict(session))

    assert restored.session_id == "s1"
    assert restored.user_id == "u1"
    assert restored.messages[0].content == "hello"
    assert restored.checkpoints[0].checkpoint_id == "c1"


def test_archive_payload_contains_summary() -> None:
    session = CopilotSession(session_id="s1", user_id="u1")
    checkpoint = CopilotCheckpoint(checkpoint_id="c1", parent_checkpoint_id=None)

    payload = archive_payload(session, [checkpoint], project="fusion-mark", env="test")

    assert payload["project"] == "fusion-mark"
    assert payload["env"] == "test"
    assert payload["summary"]["checkpoint_count"] == 1
