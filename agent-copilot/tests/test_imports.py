from app.core.service import CopilotCoreService
from app.main import create_app
from app.storage.message_store import MessageStore
from app.storage.session_store import InMemoryCopilotSessionStore


def test_module_imports() -> None:
    app = create_app()
    assert app.title == "agent-copilot"

    session_store = InMemoryCopilotSessionStore()
    service = CopilotCoreService(session_store)
    assert isinstance(service.message_store, MessageStore)
