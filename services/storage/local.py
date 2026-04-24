"""
Local Storage Provider

本地文件系统存储实现，开发环境默认使用。
保持与原有本地目录行为一致，同时兼容 StorageProvider 接口。
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List

from .base import StorageProvider, StorageObject


class LocalStorageProvider(StorageProvider):
    """本地文件系统存储提供者"""

    def __init__(self, root_dir: str = "storage"):
        """
        初始化本地存储提供者

        Args:
            root_dir: 本地存储根目录，默认 "storage"
        """
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _to_local_path(self, key: str) -> Path:
        """将存储 key 转换为本地文件路径"""
        # 安全性：限制在 root_dir 内，防止路径穿越
        local_path = self.root_dir / key
        try:
            local_path.resolve().relative_to(self.root_dir.resolve())
        except ValueError:
            raise ValueError(f"Invalid storage key: {key}")
        return local_path

    def save_file(self, key: str, file_path: str, metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        """将本地文件复制到存储目录"""
        src = Path(file_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        dst = self._to_local_path(key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))

        stat = dst.stat()
        content_type = self._guess_content_type(key)

        return StorageObject(
            key=key,
            size=stat.st_size,
            content_type=content_type,
            metadata=metadata or {},
            url=dst.as_uri()
        )

    def save_bytes(self, key: str, data: bytes, content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        """将字节数据写入存储目录"""
        dst = self._to_local_path(key)
        dst.parent.mkdir(parents=True, exist_ok=True)

        with open(dst, "wb") as f:
            f.write(data)

        content_type = content_type or self._guess_content_type(key)

        return StorageObject(
            key=key,
            size=len(data),
            content_type=content_type,
            metadata=metadata or {},
            url=dst.as_uri()
        )

    def read_url(self, key: str) -> Optional[str]:
        """获取本地文件 URI"""
        local_path = self._to_local_path(key)
        if local_path.exists():
            return local_path.as_uri()
        return None

    def read_bytes(self, key: str) -> Optional[bytes]:
        """读取本地文件内容"""
        local_path = self._to_local_path(key)
        if not local_path.exists():
            return None
        with open(local_path, "rb") as f:
            return f.read()

    def list_keys(self, prefix: str) -> List[str]:
        """列出指定前缀下的所有文件 keys"""
        search_dir = self._to_local_path(prefix)
        if not search_dir.exists():
            return []

        results = []
        # 如果 prefix 本身是一个文件，直接返回
        if search_dir.is_file():
            return [prefix]

        for file_path in search_dir.rglob("*"):
            if file_path.is_file():
                relative = file_path.relative_to(self.root_dir).as_posix()
                results.append(relative)

        return results

    def exists(self, key: str) -> bool:
        """检查本地文件是否存在"""
        return self._to_local_path(key).exists()

    @staticmethod
    def _guess_content_type(key: str) -> str:
        """根据文件扩展名猜测 content type"""
        ext = Path(key).suffix.lower()
        mapping = {
            ".pdf": "application/pdf",
            ".md": "text/markdown",
            ".json": "application/json",
            ".jsonl": "application/jsonlines",
            ".html": "text/html",
            ".htm": "text/html",
            ".txt": "text/plain",
            ".yaml": "application/yaml",
            ".yml": "application/yaml",
            ".zip": "application/zip",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        return mapping.get(ext, "application/octet-stream")
