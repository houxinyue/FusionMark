"""
Storage provider tests that do not depend on ambient machine env vars.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def test_local_provider():
    from services.storage.local import LocalStorageProvider

    with tempfile.TemporaryDirectory() as tmpdir:
        provider = LocalStorageProvider(root_dir=tmpdir)

        test_file = Path(tmpdir) / "source.txt"
        test_file.write_text("hello world", encoding="utf-8")

        obj = provider.save_file("tasks/test-001/hello.txt", str(test_file))
        assert obj.key == "tasks/test-001/hello.txt"
        assert obj.size == 11
        assert obj.content_type == "text/plain"
        assert obj.url.startswith("file://")

        assert provider.exists("tasks/test-001/hello.txt")
        assert not provider.exists("tasks/test-001/not_exist.txt")

        data = provider.read_bytes("tasks/test-001/hello.txt")
        assert data == b"hello world"
        assert provider.read_bytes("nonexistent") is None

        url = provider.read_url("tasks/test-001/hello.txt")
        assert url and url.startswith("file://")
        assert provider.read_url("nonexistent") is None

        obj2 = provider.save_bytes(
            "tasks/test-001/data.bin",
            b"\x00\x01\x02",
            content_type="application/octet-stream",
        )
        assert obj2.size == 3
        assert provider.read_bytes("tasks/test-001/data.bin") == b"\x00\x01\x02"

        keys = provider.list_keys("tasks/test-001")
        assert len(keys) == 2
        assert "tasks/test-001/hello.txt" in keys
        assert "tasks/test-001/data.bin" in keys

        src_dir = Path(tmpdir) / "src_dir"
        src_dir.mkdir()
        (src_dir / "a.md").write_text("# A", encoding="utf-8")
        (src_dir / "sub").mkdir()
        (src_dir / "sub" / "b.json").write_text('{"b": 1}', encoding="utf-8")

        saved = provider.save_directory("tasks/test-002/src", str(src_dir))
        assert len(saved) == 2

        keys2 = provider.list_keys("tasks/test-002/src")
        assert len(keys2) == 2

        try:
            provider.save_file("../../../etc/passwd", str(test_file))
            assert False, "expected path traversal rejection"
        except ValueError:
            pass


def test_factory():
    from services.storage.factory import StorageFactory
    from services.storage.local import LocalStorageProvider

    old_provider = os.getenv("STORAGE_PROVIDER")

    try:
        StorageFactory.reset()
        os.environ["STORAGE_PROVIDER"] = "local"
        provider = StorageFactory.get_provider()
        assert isinstance(provider, LocalStorageProvider)

        os.environ["STORAGE_PROVIDER"] = "minio"
        StorageFactory.reset()

        try:
            provider2 = StorageFactory.get_provider()
            assert provider2 is not None
        except Exception:
            pass
    finally:
        if old_provider is None:
            os.environ.pop("STORAGE_PROVIDER", None)
        else:
            os.environ["STORAGE_PROVIDER"] = old_provider
        StorageFactory.reset()


def test_integration():
    from services.storage import get_storage_provider
    from services.storage.factory import StorageFactory

    old_provider = os.getenv("STORAGE_PROVIDER")
    old_root = os.getenv("LOCAL_STORAGE_ROOT")

    StorageFactory.reset()
    os.environ["STORAGE_PROVIDER"] = "local"
    os.environ["LOCAL_STORAGE_ROOT"] = tempfile.mkdtemp(prefix="fusion_mark_test_")
    StorageFactory.reset()

    try:
        provider = get_storage_provider()
        tmp = Path(os.environ["LOCAL_STORAGE_ROOT"])

        mineru_dir = tmp / "mineru_output" / "task-abc"
        mineru_dir.mkdir(parents=True)
        (mineru_dir / "full.md").write_text("# Markdown content", encoding="utf-8")
        (mineru_dir / "layout.json").write_text("{}", encoding="utf-8")

        saved = provider.save_directory("tasks/task-abc/mineru/extracted", str(mineru_dir))
        assert len(saved) == 2

        debug_dir = tmp / "highlight_output" / "debug"
        debug_dir.mkdir(parents=True)
        (debug_dir / "extractions.jsonl").write_text('{"text": "test"}\n', encoding="utf-8")
        (debug_dir / "langextract_visual.html").write_text("<html></html>", encoding="utf-8")

        saved2 = provider.save_directory("tasks/task-abc/langextract", str(debug_dir))
        assert len(saved2) == 2

        pdf_path = tmp / "highlight_output" / "task-abc_highlighted.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")

        key = "tasks/task-abc/highlight/task-abc_highlighted.pdf"
        obj = provider.save_file(key, str(pdf_path))
        assert obj.key == key

        all_keys = provider.list_keys("tasks/task-abc")
        assert len(all_keys) == 5

        url = provider.read_url(key)
        assert url and url.startswith("file://")
    finally:
        shutil.rmtree(os.environ["LOCAL_STORAGE_ROOT"], ignore_errors=True)
        if old_root is None:
            os.environ.pop("LOCAL_STORAGE_ROOT", None)
        else:
            os.environ["LOCAL_STORAGE_ROOT"] = old_root
        if old_provider is None:
            os.environ.pop("STORAGE_PROVIDER", None)
        else:
            os.environ["STORAGE_PROVIDER"] = old_provider
        StorageFactory.reset()
