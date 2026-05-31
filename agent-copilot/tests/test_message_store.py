from app.models.session import CopilotMessage
from app.storage.message_store import MessageStore
from app.storage.session_store import InMemoryCopilotSessionStore


def test_message_store_appends_and_lists_messages() -> None:
    session_store = InMemoryCopilotSessionStore()
    session = session_store.create("u1")
    store = MessageStore(session_store)

    first = store.append_user_message(session.session_id, "hello")
    second = store.append_assistant_message(session.session_id, "world")

    messages = store.list(session.session_id)

    assert first.role == "user"
    assert second.role == "assistant"
    assert [message.content for message in messages] == ["hello", "world"]
    assert all(isinstance(message, CopilotMessage) for message in messages)
