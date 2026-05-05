"""
MinIO Storage Provider

对象存储实现，生产环境推荐。
通过环境变量配置 MinIO 连接参数。

依赖: pip install minio
"""

import os
from pathlib import Path
from typing import Optional, Dict, List

from .base import StorageProvider, StorageObject


class MinioStorageProvider(StorageProvider):
    """MinIO 对象存储提供者"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
        region: Optional[str] = None,
        prefix: str = "fusion-mark"
    ):
        """
        初始化 MinIO 存储提供者

        Args:
            endpoint: MinIO 服务端点，如 "127.0.0.1:9000"
            access_key: 访问密钥
            secret_key: 秘密密钥
            bucket: 存储桶名称
            secure: 是否使用 HTTPS
            region: 区域名称（可选）
            prefix: key 前缀，默认 "fusion-mark"
        """
        try:
            from minio import Minio
        except ImportError as e:
            raise ImportError(
                "MinIO provider requires 'minio' package. "
                "Install it with: pip install minio"
            ) from e

        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region
        )
        self.bucket = bucket
        self.prefix = prefix.strip("/")

        # 确保 bucket 存在
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def _full_key(self, key: str) -> str:
        """拼接前缀与 key"""
        key = key.lstrip("/")
        if self.prefix:
            return f"{self.prefix}/{key}"
        return key

    def _strip_prefix(self, full_key: str) -> str:
        """从完整 key 中移除前缀，返回业务 key"""
        prefix_with_slash = f"{self.prefix}/"
        if self.prefix and full_key.startswith(prefix_with_slash):
            return full_key[len(prefix_with_slash):]
        return full_key

    def save_file(self, key: str, file_path: str, metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        """上传本地文件到 MinIO"""
        from minio.commonconfig import Tags

        full_key = self._full_key(key)
        file_size = os.path.getsize(file_path)
        content_type = self._guess_content_type(key)

        tags = Tags(for_object=True)
        if metadata:
            for k, v in metadata.items():
                tags[k] = v

        self.client.fput_object(
            self.bucket,
            full_key,
            file_path,
            content_type=content_type,
            tags=tags if tags else None
        )

        # 生成 presigned URL（默认 7 天有效）
        url = self.client.presigned_get_object(self.bucket, full_key)

        return StorageObject(
            key=key,
            size=file_size,
            content_type=content_type,
            metadata=metadata or {},
            url=url
        )

    def save_bytes(self, key: str, data: bytes, content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        """上传字节数据到 MinIO"""
        from io import BytesIO
        from minio.commonconfig import Tags

        full_key = self._full_key(key)
        content_type = content_type or self._guess_content_type(key)

        tags = Tags(for_object=True)
        if metadata:
            for k, v in metadata.items():
                tags[k] = v

        self.client.put_object(
            self.bucket,
            full_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
            tags=tags if tags else None
        )

        url = self.client.presigned_get_object(self.bucket, full_key)

        return StorageObject(
            key=key,
            size=len(data),
            content_type=content_type,
            metadata=metadata or {},
            url=url
        )

    def read_url(self, key: str) -> Optional[str]:
        """获取 MinIO presigned URL"""
        full_key = self._full_key(key)
        try:
            return self.client.presigned_get_object(self.bucket, full_key)
        except Exception:
            return None

    def read_bytes(self, key: str) -> Optional[bytes]:
        """从 MinIO 下载对象内容"""
        full_key = self._full_key(key)
        try:
            response = self.client.get_object(self.bucket, full_key)
            return response.read()
        except Exception:
            return None

    def list_keys(self, prefix: str) -> List[str]:
        """列出指定前缀下的对象 keys"""
        full_prefix = self._full_key(prefix)
        objects = self.client.list_objects(self.bucket, prefix=full_prefix, recursive=True)
        return [self._strip_prefix(obj.object_name) for obj in objects]

    def exists(self, key: str) -> bool:
        """检查对象是否在 MinIO 中存在"""
        full_key = self._full_key(key)
        try:
            self.client.stat_object(self.bucket, full_key)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete one MinIO storage object."""
        full_key = self._full_key(key)
        try:
            self.client.remove_object(self.bucket, full_key)
            return True
        except Exception:
            return False

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
