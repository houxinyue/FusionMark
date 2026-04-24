"""
Storage Provider 本地验证脚本

运行方式:
    cd E:/dolt/data/fusion-mark
    uv run python services/storage/test_storage_provider.py

验证内容:
    1. LocalStorageProvider 基础功能
    2. StorageFactory 环境变量读取
    3. save_file / save_bytes / read_url / read_bytes / list_keys / exists
    4. save_directory 批量保存
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 将项目根目录加入路径，确保可以导入 services 包
_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def test_local_provider():
    """测试 LocalStorageProvider"""
    from services.storage.local import LocalStorageProvider

    with tempfile.TemporaryDirectory() as tmpdir:
        provider = LocalStorageProvider(root_dir=tmpdir)

        # 1. save_file
        test_file = Path(tmpdir) / "source.txt"
        test_file.write_text("hello world", encoding="utf-8")

        obj = provider.save_file("tasks/test-001/hello.txt", str(test_file))
        assert obj.key == "tasks/test-001/hello.txt"
        assert obj.size == 11
        assert obj.content_type == "text/plain"
        assert obj.url.startswith("file://")
        print(f"[OK] save_file: key={obj.key}, size={obj.size}, url={obj.url}")

        # 2. exists
        assert provider.exists("tasks/test-001/hello.txt")
        assert not provider.exists("tasks/test-001/not_exist.txt")
        print("[OK] exists 检查通过")

        # 3. read_bytes
        data = provider.read_bytes("tasks/test-001/hello.txt")
        assert data == b"hello world"
        assert provider.read_bytes("nonexistent") is None
        print("[OK] read_bytes 通过")

        # 4. read_url
        url = provider.read_url("tasks/test-001/hello.txt")
        assert url and url.startswith("file://")
        assert provider.read_url("nonexistent") is None
        print(f"[OK] read_url: {url}")

        # 5. save_bytes
        obj2 = provider.save_bytes("tasks/test-001/data.bin", b"\x00\x01\x02", content_type="application/octet-stream")
        assert obj2.size == 3
        assert provider.read_bytes("tasks/test-001/data.bin") == b"\x00\x01\x02"
        print("[OK] save_bytes 通过")

        # 6. list_keys
        keys = provider.list_keys("tasks/test-001")
        assert len(keys) == 2
        assert "tasks/test-001/hello.txt" in keys
        assert "tasks/test-001/data.bin" in keys
        print(f"[OK] list_keys: {keys}")

        # 7. save_directory
        src_dir = Path(tmpdir) / "src_dir"
        src_dir.mkdir()
        (src_dir / "a.md").write_text("# A")
        (src_dir / "sub").mkdir()
        (src_dir / "sub" / "b.json").write_text('{"b": 1}')

        saved = provider.save_directory("tasks/test-002/src", str(src_dir))
        assert len(saved) == 2
        print(f"[OK] save_directory: 保存了 {len(saved)} 个文件")

        keys2 = provider.list_keys("tasks/test-002/src")
        assert len(keys2) == 2
        print(f"[OK] list_keys after directory save: {keys2}")

        # 8. 安全性测试：路径穿越应报错
        try:
            provider.save_file("../../../etc/passwd", str(test_file))
            assert False, "应抛出路径穿越异常"
        except ValueError as e:
            print(f"[OK] 路径穿越防护生效: {e}")

    print("\n[全部通过] LocalStorageProvider 验证完成")


def test_factory():
    """测试 StorageFactory"""
    from services.storage.factory import StorageFactory

    # 重置缓存
    StorageFactory.reset()

    # 默认应为 local
    provider = StorageFactory.get_provider()
    from services.storage.local import LocalStorageProvider
    assert isinstance(provider, LocalStorageProvider)
    print(f"[OK] 默认 provider 为 local: {type(provider).__name__}")

    # 切换环境变量测试 minio（不真正连接，仅测试构造逻辑）
    old_provider = os.getenv("STORAGE_PROVIDER")
    os.environ["STORAGE_PROVIDER"] = "minio"
    StorageFactory.reset()

    try:
        provider2 = StorageFactory.get_provider()
        # 如果没有 minio 包会抛 ImportError；如果 minio 未启动会抛连接异常
        print(f"[OK] minio provider 创建: {type(provider2).__name__}")
    except Exception as e:
        print(f"[OK] minio provider 预期异常（未启动或服务不可达）: {type(e).__name__}")
    finally:
        if old_provider is None:
            os.environ.pop("STORAGE_PROVIDER", None)
        else:
            os.environ["STORAGE_PROVIDER"] = old_provider
        StorageFactory.reset()

    print("\n[全部通过] StorageFactory 验证完成")


def test_integration():
    """
    模拟 task_processor 中的集成场景：
    保存 MinerU extracted 目录、LangExtract 产物、Highlight PDF
    """
    from services.storage import get_storage_provider
    from services.storage.factory import StorageFactory

    StorageFactory.reset()
    os.environ["LOCAL_STORAGE_ROOT"] = tempfile.mkdtemp(prefix="fusion_mark_test_")
    StorageFactory.reset()

    try:
        provider = get_storage_provider()
        tmp = Path(os.environ["LOCAL_STORAGE_ROOT"])

        # 模拟 MinerU extracted 目录
        mineru_dir = tmp / "mineru_output" / "task-abc"
        mineru_dir.mkdir(parents=True)
        (mineru_dir / "full.md").write_text("# Markdown content")
        (mineru_dir / "layout.json").write_text('{}')

        prefix = "tasks/task-abc/mineru/extracted"
        saved = provider.save_directory(prefix, str(mineru_dir))
        assert len(saved) == 2
        print(f"[OK] MinerU 产物持久化: {len(saved)} 个文件")

        # 模拟 LangExtract debug 目录
        debug_dir = tmp / "highlight_output" / "debug"
        debug_dir.mkdir(parents=True)
        (debug_dir / "extractions.jsonl").write_text('{"text": "test"}\n')
        (debug_dir / "langextract_visual.html").write_text("<html></html>")

        prefix2 = "tasks/task-abc/langextract"
        saved2 = provider.save_directory(prefix2, str(debug_dir))
        assert len(saved2) == 2
        print(f"[OK] LangExtract 产物持久化: {len(saved2)} 个文件")

        # 模拟 Highlight PDF
        pdf_path = tmp / "highlight_output" / "task-abc_highlighted.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")

        key = "tasks/task-abc/highlight/task-abc_highlighted.pdf"
        obj = provider.save_file(key, str(pdf_path))
        assert obj.key == key
        print(f"[OK] Highlight PDF 持久化: {obj.key}, size={obj.size}")

        # 验证 list_keys
        all_keys = provider.list_keys("tasks/task-abc")
        assert len(all_keys) == 5
        print(f"[OK] 总产物数量: {len(all_keys)}")

        # 验证 read_url
        url = provider.read_url(key)
        assert url and url.startswith("file://")
        print(f"[OK] read_url: {url}")

    finally:
        shutil.rmtree(os.environ["LOCAL_STORAGE_ROOT"], ignore_errors=True)
        del os.environ["LOCAL_STORAGE_ROOT"]
        StorageFactory.reset()

    print("\n[全部通过] 集成场景验证完成")


if __name__ == "__main__":
    print("=" * 60)
    print("Storage Provider 本地验证")
    print("=" * 60)

    test_local_provider()
    print()
    test_factory()
    print()
    test_integration()

    print("\n" + "=" * 60)
    print("SUCCESS 所有验证通过")
    print("=" * 60)
