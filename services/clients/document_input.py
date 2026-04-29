"""
Document input resolution for MinerU providers.

The resolver turns public task input into a provider-compatible source:
HTTP(S) URLs are passed through, storage object keys are materialized into the
task workspace, and local files are validated before use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

try:
    from services.storage import get_storage_provider
    from services.storage.workspace import get_workspace_dir
except ImportError:  # pragma: no cover - supports running from services/
    from ..storage import get_storage_provider
    from ..storage.workspace import get_workspace_dir


class DocumentInputResolutionError(ValueError):
    """Raised when a document input cannot be resolved safely."""


@dataclass(frozen=True)
class ResolvedDocumentInput:
    """Provider-ready document input."""

    source: str
    source_type: str
    original: str
    materialized_path: Optional[Path] = None


@dataclass(frozen=True)
class DocumentInputResolverConfig:
    """Options controlling document source resolution."""

    enable_storage_input: bool = True
    enable_local_input: bool = True
    storage_uri_schemes: tuple[str, ...] = ("storage", "object", "minio")
    local_uri_schemes: tuple[str, ...] = ("file", "local")


class DocumentInputResolver:
    """Resolve URL, storage-key, and local-file document sources."""

    _SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

    def __init__(self, config: Optional[DocumentInputResolverConfig] = None):
        self.config = config or DocumentInputResolverConfig()

    def resolve(self, source: str, task_id: str) -> ResolvedDocumentInput:
        source = (source or "").strip()
        if not source:
            raise DocumentInputResolutionError("Document source cannot be empty")

        parsed = urlparse(source)
        if parsed.scheme in ("http", "https"):
            return ResolvedDocumentInput(source=source, source_type="url", original=source)

        if parsed.scheme in self.config.storage_uri_schemes:
            key = self._storage_key_from_uri(parsed)
            return self._materialize_storage_key(key, task_id, source)

        if parsed.scheme in self.config.local_uri_schemes:
            local_path = self._local_path_from_uri(parsed)
            return self._validate_local_file(local_path, source)

        bare_path = Path(source)
        if self.config.enable_local_input and bare_path.exists():
            return self._validate_local_file(bare_path, source)

        if self.config.enable_storage_input:
            provider = get_storage_provider()
            if provider.exists(source):
                return self._materialize_storage_key(source, task_id, source)

        raise DocumentInputResolutionError(
            "Unsupported document source. Use an HTTP(S) URL, storage:// object key, "
            "or an existing local file path."
        )

    def _materialize_storage_key(
        self,
        key: str,
        task_id: str,
        original: str,
    ) -> ResolvedDocumentInput:
        if not self.config.enable_storage_input:
            raise DocumentInputResolutionError("Storage document input is disabled")

        provider = get_storage_provider()
        data = provider.read_bytes(key)
        if data is None:
            raise DocumentInputResolutionError(f"Storage object not found: {key}")

        input_dir = get_workspace_dir(task_id) / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        filename = self._safe_filename(Path(key).name or "document")
        target = input_dir / filename
        target.write_bytes(data)

        return ResolvedDocumentInput(
            source=str(target),
            source_type="storage",
            original=original,
            materialized_path=target,
        )

    def _validate_local_file(self, path: Path, original: str) -> ResolvedDocumentInput:
        if not self.config.enable_local_input:
            raise DocumentInputResolutionError("Local file document input is disabled")

        resolved = path.expanduser().resolve()
        if not resolved.exists() or not resolved.is_file():
            raise DocumentInputResolutionError(f"Local document file not found: {path}")

        return ResolvedDocumentInput(
            source=str(resolved),
            source_type="local",
            original=original,
            materialized_path=resolved,
        )

    def _storage_key_from_uri(self, parsed) -> str:
        key = f"{parsed.netloc}{parsed.path}".lstrip("/")
        key = unquote(key)
        if not key:
            raise DocumentInputResolutionError("Storage document key cannot be empty")
        return key

    def _local_path_from_uri(self, parsed) -> Path:
        if parsed.scheme == "file":
            value = unquote(parsed.path)
            if re.match(r"^/[A-Za-z]:/", value):
                value = value[1:]
            return Path(value)
        value = f"{parsed.netloc}{parsed.path}" if parsed.netloc else parsed.path
        return Path(unquote(value))

    def _safe_filename(self, value: str) -> str:
        cleaned = self._SAFE_FILENAME_RE.sub("_", value).strip("._")
        return cleaned or "document"
