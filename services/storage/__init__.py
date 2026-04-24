"""
Storage Provider 模块

统一存储抽象，支持 local 与 minio provider。

使用方式:
    from services.storage import get_storage_provider
    provider = get_storage_provider()
    obj = provider.save_file("tasks/xxx/highlight/output.pdf", "./highlight_output/output.pdf")
"""

from .base import StorageProvider, StorageObject
from .factory import StorageFactory, get_storage_provider
from .local import LocalStorageProvider
from .workspace import (
    get_workspace_dir,
    get_mineru_workspace,
    get_highlight_workspace,
    cleanup_workspace,
    should_cleanup_workspace,
)

__all__ = [
    "StorageProvider",
    "StorageObject",
    "StorageFactory",
    "get_storage_provider",
    "LocalStorageProvider",
    "get_workspace_dir",
    "get_mineru_workspace",
    "get_highlight_workspace",
    "cleanup_workspace",
    "should_cleanup_workspace",
]
