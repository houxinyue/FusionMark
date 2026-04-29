import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest

from services.clients.mineru import MinerUConfig, MinerUClient
from services.clients.mineru_provider import (
    LegacyV4MinerUProvider,
    MinerUProviderError,
    MinerUProviderFactory,
    OpenSdkMinerUProvider,
)


@dataclass
class FakeProgress:
    extracted_pages: int = 1
    total_pages: int = 2
    start_time: str = "2026-04-29T00:00:00Z"


class FakeSdkResult:
    task_id = "sdk-task-1"
    state = "done"
    error = None
    zip_url = "https://example.com/result.zip"
    progress = FakeProgress()
    markdown = "# Parsed"
    html = "<h1>Parsed</h1>"
    latex = None
    docx = None

    def save_all(self, directory):
        Path(directory, "official.json").write_text("{}", encoding="utf-8")


class FakeMinerU:
    def __init__(self, token=None, base_url=None):
        self.token = token
        self.base_url = base_url

    def submit(self, source, **kwargs):
        self.source = source
        self.kwargs = kwargs
        return "batch-1"

    def get_batch(self, batch_id):
        return [FakeSdkResult()]


def test_factory_rejects_unknown_provider():
    config = MinerUConfig(api_key="key", provider_mode="bad-mode")

    with pytest.raises(MinerUProviderError):
        MinerUProviderFactory.create(config)


def test_factory_creates_legacy_provider():
    config = MinerUConfig(api_key="key", provider_mode="legacy_v4")

    assert isinstance(MinerUProviderFactory.create(config), LegacyV4MinerUProvider)


def test_open_sdk_provider_normalizes_result_and_saves_artifacts(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "mineru", types.SimpleNamespace(MinerU=FakeMinerU))
    config = MinerUConfig(
        api_key="key",
        output_dir=str(tmp_path / "extract"),
        provider_mode="open_sdk",
        poll_interval=0,
        max_poll_retries=1,
        sdk_extra_formats=["html"],
    )
    provider = OpenSdkMinerUProvider(config)
    progress_events = []

    result = provider.process_document(
        source="https://example.com/doc.pdf",
        model_version=MinerUClient.MODEL_HTML,
        is_ocr=True,
        enable_formula=True,
        enable_table=True,
        language="ch",
        wait_callback=lambda attempt, state, data: progress_events.append((attempt, state, data)),
    )

    assert result is not None
    assert result.state == "done"
    assert result.task_id == "sdk-task-1"
    assert result.content == "# Parsed"
    assert (tmp_path / "extract" / "full.md").read_text(encoding="utf-8") == "# Parsed"
    assert (tmp_path / "extract" / "official.json").exists()
    assert (tmp_path / "extract" / "open_sdk_result.json").exists()
    assert progress_events[0][1] == "done"
    assert progress_events[0][2]["extract_progress"]["total_pages"] == 2
