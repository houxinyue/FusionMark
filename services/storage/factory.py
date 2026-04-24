"""
Storage Provider 工厂

根据环境变量自动创建对应的 StorageProvider 实例。
"""

import os
from typing import Optional

from .base import StorageProvider
from .local import LocalStorageProvider


class StorageFactory:
    """存储提供者工厂"""

    _instance: Optional[StorageProvider] = None

    @classmethod
    def get_provider(cls) -> StorageProvider:
        """
        获取全局单例 StorageProvider 实例

        首次调用时根据环境变量创建，后续直接返回缓存实例。

        环境变量:
            STORAGE_PROVIDER: local | minio (默认 local)
            LOCAL_STORAGE_ROOT: 本地存储根目录 (默认 storage)

            MINIO_ENDPOINT: MinIO 端点
            MINIO_ACCESS_KEY: MinIO 访问密钥
            MINIO_SECRET_KEY: MinIO 秘密密钥
            MINIO_BUCKET: MinIO 存储桶
            MINIO_SECURE: 是否使用 HTTPS (默认 false)
            MINIO_REGION: MinIO 区域 (可选)
            MINIO_PREFIX: MinIO key 前缀 (默认 fusion-mark)

        Returns:
            StorageProvider 实例
        """
        if cls._instance is not None:
            return cls._instance

        provider_type = os.getenv("STORAGE_PROVIDER", "local").lower().strip()

        if provider_type == "minio":
            cls._instance = cls._create_minio_provider()
        else:
            cls._instance = cls._create_local_provider()

        return cls._instance

    @classmethod
    def _create_local_provider(cls) -> LocalStorageProvider:
        """创建本地存储提供者"""
        root_dir = os.getenv("LOCAL_STORAGE_ROOT", "storage")
        return LocalStorageProvider(root_dir=root_dir)

    @classmethod
    def _create_minio_provider(cls) -> StorageProvider:
        """创建 MinIO 存储提供者"""
        from .minio_provider import MinioStorageProvider

        endpoint = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        bucket = os.getenv("MINIO_BUCKET", "fusion-mark")
        secure = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")
        region = os.getenv("MINIO_REGION") or None
        prefix = os.getenv("MINIO_PREFIX", "fusion-mark")

        return MinioStorageProvider(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket,
            secure=secure,
            region=region,
            prefix=prefix
        )

    @classmethod
    def reset(cls):
        """重置工厂缓存（主要用于测试）"""
        cls._instance = None


# 便捷函数
def get_storage_provider() -> StorageProvider:
    """获取当前配置的 StorageProvider 实例"""
    return StorageFactory.get_provider()
