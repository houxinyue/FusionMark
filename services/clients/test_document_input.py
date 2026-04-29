from pathlib import Path

import pytest

from services.clients import document_input
from services.clients.document_input import (
    DocumentInputResolutionError,
    DocumentInputResolver,
)


class FakeStorageProvider:
    def __init__(self, objects):
        self.objects = objects

    def exists(self, key):
        return key in self.objects

    def read_bytes(self, key):
        return self.objects.get(key)


def test_resolver_passes_http_url_through():
    resolved = DocumentInputResolver().resolve("https://example.com/a.pdf", "task-1")

    assert resolved.source == "https://example.com/a.pdf"
    assert resolved.source_type == "url"
    assert resolved.materialized_path is None


def test_resolver_validates_local_path(tmp_path):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF")

    resolved = DocumentInputResolver().resolve(str(pdf), "task-1")

    assert Path(resolved.source) == pdf.resolve()
    assert resolved.source_type == "local"


def test_resolver_materializes_storage_key(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path / "workspaces"))
    monkeypatch.setattr(
        document_input,
        "get_storage_provider",
        lambda: FakeStorageProvider({"tasks/input/doc.pdf": b"%PDF"}),
    )

    resolved = DocumentInputResolver().resolve("storage://tasks/input/doc.pdf", "task-1")

    assert resolved.source_type == "storage"
    assert resolved.materialized_path is not None
    assert resolved.materialized_path.read_bytes() == b"%PDF"
    assert resolved.materialized_path.parent == tmp_path / "workspaces" / "task-1" / "input"


def test_resolver_rejects_unknown_source(monkeypatch):
    monkeypatch.setattr(document_input, "get_storage_provider", lambda: FakeStorageProvider({}))

    with pytest.raises(DocumentInputResolutionError):
        DocumentInputResolver().resolve("not-a-known-source.pdf", "task-1")
