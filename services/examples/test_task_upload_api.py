from types import SimpleNamespace

from fastapi.testclient import TestClient

from services.api import server


class FakeTaskStore:
    def __init__(self):
        self.created = []

    def create_task(self, task_id, document_url):
        self.created.append((task_id, document_url))


class FakeStorageProvider:
    def __init__(self):
        self.saved = []

    def save_file(self, key, file_path, metadata=None):
        self.saved.append((key, file_path, metadata or {}))
        return SimpleNamespace(key=key, size=1, url=f"fake://{key}")


def test_upload_task_saves_file_and_schedules_storage_source(monkeypatch, tmp_path):
    store = FakeTaskStore()
    storage = FakeStorageProvider()
    scheduled = []

    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path / "workspaces"))
    monkeypatch.setattr(server, "get_task_store", lambda: store)
    monkeypatch.setattr(
        server,
        "_get_effective_pipeline_config",
        lambda: SimpleNamespace(mineru_client_mode="open_sdk"),
    )
    monkeypatch.setattr("services.storage.get_storage_provider", lambda: storage)

    def fake_process_pdf_task(**kwargs):
        scheduled.append(kwargs)

    monkeypatch.setattr(server, "process_pdf_task", fake_process_pdf_task)

    client = TestClient(server.app)
    response = client.post(
        "/api/v1/tasks/upload",
        files={"file": ("report.pdf", b"%PDF-1.4", "application/pdf")},
        data={"model": "vlm", "language": "ch"},
    )

    assert response.status_code == 200
    body = response.json()
    task_id = body["task_id"]
    expected_source = f"storage://tasks/{task_id}/input/report.pdf"

    assert storage.saved[0][0] == f"tasks/{task_id}/input/report.pdf"
    assert storage.saved[0][2]["source"] == "task_upload"
    assert store.created == [(task_id, expected_source)]
    assert scheduled[0]["document_url"] == expected_source
    assert scheduled[0]["model"] == "vlm"


def test_upload_task_persists_with_local_storage_provider(monkeypatch, tmp_path):
    from services.storage.factory import StorageFactory

    store = FakeTaskStore()
    scheduled = []
    storage_root = tmp_path / "storage"

    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path / "workspaces"))
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(storage_root))
    StorageFactory.reset()
    monkeypatch.setattr(server, "get_task_store", lambda: store)
    monkeypatch.setattr(
        server,
        "_get_effective_pipeline_config",
        lambda: SimpleNamespace(mineru_client_mode="open_sdk"),
    )
    monkeypatch.setattr(server, "process_pdf_task", lambda **kwargs: scheduled.append(kwargs))

    try:
        client = TestClient(server.app)
        response = client.post(
            "/api/v1/tasks/upload",
            files={"file": ("local.pdf", b"%PDF-1.4 local", "application/pdf")},
        )

        assert response.status_code == 200
        task_id = response.json()["task_id"]
        stored_file = storage_root / "tasks" / task_id / "input" / "local.pdf"
        assert stored_file.read_bytes() == b"%PDF-1.4 local"
        assert scheduled[0]["document_url"] == f"storage://tasks/{task_id}/input/local.pdf"
    finally:
        StorageFactory.reset()


def test_upload_task_rejects_unsupported_extension(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path / "workspaces"))
    monkeypatch.setattr(
        server,
        "_get_effective_pipeline_config",
        lambda: SimpleNamespace(mineru_client_mode="open_sdk"),
    )

    client = TestClient(server.app)
    response = client.post(
        "/api/v1/tasks/upload",
        files={"file": ("payload.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported upload file type" in response.json()["detail"]


def test_upload_task_rejects_empty_file(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path / "workspaces"))
    monkeypatch.setattr(
        server,
        "_get_effective_pipeline_config",
        lambda: SimpleNamespace(mineru_client_mode="open_sdk"),
    )

    client = TestClient(server.app)
    response = client.post(
        "/api/v1/tasks/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
