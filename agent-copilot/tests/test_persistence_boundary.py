from app.storage import PersistenceSettings, create_in_memory_persistence


def test_persistence_boundary_creates_checkpoint_and_archive_payload() -> None:
    persistence = create_in_memory_persistence(PersistenceSettings(env="test"))
    session = persistence.create_session("u1")
    session.current_step = "validating_profile"
    session.current_draft = {"name": "paper"}
    session.pending_action = {"action": "save_profile"}
    session.last_validation_result = {"valid": True, "errors": []}
    persistence.save_session(session)
    persistence.messages.append_user_message(session.session_id, "hello")

    checkpoint = persistence.create_checkpoint(session.session_id)
    payload = persistence.archive_session(session.session_id)

    assert checkpoint.parent_checkpoint_id is None
    assert checkpoint.step == "validating_profile"
    assert checkpoint.draft_profile == {"name": "paper"}
    assert checkpoint.validation_result == {"valid": True, "errors": []}
    assert checkpoint.pending_action == {"action": "save_profile"}
    assert payload["env"] == "test"
    assert payload["current_draft"] == {"name": "paper"}
    assert payload["last_validation_result"] == {"valid": True, "errors": []}
    assert payload["summary"]["message_count"] == 1
    assert payload["summary"]["checkpoint_count"] == 1
