"""
Storage Provider 抽象基类

统一存储抽象，支持 local 与 minio provider，通过环境变量切换。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Any


@dataclass
class StorageObject:
    """存储对象元数据"""
    key: str
    size: int = 0
    content_type: str = "application/octet-stream"
    metadata: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None


class StorageProvider(ABC):
    """
    存储提供者抽象基类

    最小 API 设计，聚焦当前 artifact 需求：
    - save_file: 从本地文件路径保存到存储
    - save_bytes: 从字节数据保存到存储
    - read_url: 获取对象的访问 URL（本地为 file://，MinIO 为 presigned URL 或代理路径）
    - read_bytes: 读取对象内容
    - list_keys: 列出指定前缀下的对象 keys
    """

    @abstractmethod
    def save_file(self, key: str, file_path: str, metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        """
        将本地文件保存到存储

        Args:
            key: 存储对象 key
            file_path: 本地文件路径
            metadata: 可选元数据

        Returns:
            StorageObject 对象
        """
        pass

    @abstractmethod
    def save_bytes(self, key: str, data: bytes, content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        """
        将字节数据保存到存储

        Args:
            key: 存储对象 key
            data: 字节数据
            content_type: 内容类型
            metadata: 可选元数据

        Returns:
            StorageObject 对象
        """
        pass

    @abstractmethod
    def read_url(self, key: str) -> Optional[str]:
        """
        获取对象的访问 URL

        Args:
            key: 存储对象 key

        Returns:
            访问 URL，不存在返回 None
        """
        pass

    @abstractmethod
    def read_bytes(self, key: str) -> Optional[bytes]:
        """
        读取对象内容

        Args:
            key: 存储对象 key

        Returns:
            对象字节数据，不存在返回 None
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str) -> List[str]:
        """
        列出指定前缀下的所有对象 keys

        Args:
            prefix: key 前缀

        Returns:
            key 列表
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查对象是否存在

        Args:
            key: 存储对象 key

        Returns:
            是否存在
        """
        pass

    def save_directory(self, prefix: str, dir_path: str,
                       include_extensions: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, str]] = None) -> List[StorageObject]:
        """
        将本地目录下所有文件批量保存到存储

        Args:
            prefix: 存储 key 前缀
            dir_path: 本地目录路径
            include_extensions: 只包含指定扩展名的文件，None 表示全部
            metadata: 可选元数据

        Returns:
            保存的 StorageObject 列表
        """
        results = []
        base = Path(dir_path)
        if not base.exists() or not base.is_dir():
            return results

        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue

            if include_extensions is not None:
                if file_path.suffix.lower() not in include_extensions:
                    continue

            relative = file_path.relative_to(base).as_posix()
            key = f"{prefix}/{relative}" if prefix else relative
            obj = self.save_file(key, str(file_path), metadata=metadata)
            results.append(obj)

        return results
