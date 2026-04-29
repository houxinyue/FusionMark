"""
Provider abstraction for MinerU document parsing.

This module keeps SDK-specific behavior behind a stable ParseResult
contract consumed by the rest of FusionMark. Legacy v4 provider has
been removed; only the official open_sdk provider remains.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .mineru import MinerUClient, MinerUConfig, ParseResult


ProgressCallback = Callable[[int, str, Dict[str, Any]], Optional[bool]]


class MinerUProviderError(ValueError):
    """Raised when a provider cannot be configured or executed."""


class MinerUProvider(ABC):
    """Common interface implemented by all MinerU connection providers."""

    @abstractmethod
    def process_document(
        self,
        source: str,
        model_version: str = MinerUClient.MODEL_VLM,
        wait_callback: Optional[ProgressCallback] = None,
        **kwargs: Any,
    ) -> Optional[ParseResult]:
        """Parse a document and return a normalized result."""


class OpenSdkMinerUProvider(MinerUProvider):
    """MinerU provider backed by the official mineru-open-sdk package."""

    def __init__(self, config: MinerUConfig):
        self.config = config
        token = config.sdk_token or config.api_key
        if not token:
            raise MinerUProviderError(
                f"MinerU SDK token is not configured. Set {config.sdk_token_env} "
                "or MINERU_API_KEY."
            )

        try:
            from mineru import MinerU
        except ImportError as exc:  # pragma: no cover - covered by dependency checks
            raise MinerUProviderError(
                "mineru-open-sdk is not installed. Install it with: uv add mineru-open-sdk"
            ) from exc

        self.client = MinerU(token=token, base_url=config.sdk_base_url)

    def process_document(
        self,
        source: str,
        model_version: str = MinerUClient.MODEL_VLM,
        wait_callback: Optional[ProgressCallback] = None,
        **kwargs: Any,
    ) -> Optional[ParseResult]:
        extract_dir = Path(self.config.output_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            batch_id = self.client.submit(
                source,
                model=self._normalize_model(model_version),
                ocr=kwargs.get("is_ocr"),
                formula=kwargs.get("enable_formula"),
                table=kwargs.get("enable_table"),
                language=kwargs.get("language"),
                pages=kwargs.get("page_ranges"),
                extra_formats=self.config.sdk_extra_formats,
            )
            result = self._wait_for_result(batch_id, wait_callback)
            return self._normalize_result(result, extract_dir)
        except Exception as exc:
            return ParseResult(
                task_id="",
                state=MinerUClient.STATE_FAILED,
                zip_url="",
                zip_path="",
                extract_dir=str(extract_dir),
                error_msg=f"MinerU Open SDK parsing failed: {exc}",
            )

    def _wait_for_result(self, batch_id: str, callback: Optional[ProgressCallback]):
        max_retries = self.config.max_poll_retries
        interval = self.config.poll_interval
        is_infinite = max_retries <= 0
        attempt = 0

        while is_infinite or attempt < max_retries:
            attempt += 1
            results = self.client.get_batch(batch_id)
            result = results[0] if results else None
            if result is None:
                state = "pending"
                data: Dict[str, Any] = {}
            else:
                state = getattr(result, "state", "unknown")
                data = self._progress_payload(result)

            if callback:
                should_continue = callback(attempt, state, data)
                if should_continue is False:
                    raise MinerUProviderError("MinerU polling stopped by callback")

            if result is not None and state in ("done", "failed"):
                return result

            time.sleep(interval)

        raise TimeoutError(f"MinerU SDK polling timed out after {max_retries} attempts")

    def _normalize_result(self, result: Any, extract_dir: Path) -> ParseResult:
        task_id = getattr(result, "task_id", "")
        state = getattr(result, "state", "unknown")
        error_msg = getattr(result, "error", None)
        zip_url = getattr(result, "zip_url", None) or ""
        content = getattr(result, "markdown", None)

        if state == "failed":
            self._write_debug_metadata(result, extract_dir)
            return ParseResult(
                task_id=task_id,
                state=state,
                zip_url=zip_url,
                zip_path="",
                extract_dir=str(extract_dir),
                error_msg=error_msg or "MinerU Open SDK task failed",
            )

        if state != "done":
            return ParseResult(
                task_id=task_id,
                state=state,
                zip_url=zip_url,
                zip_path="",
                extract_dir=str(extract_dir),
                error_msg=f"MinerU Open SDK task ended with non-terminal success state: {state}",
            )

        self._save_sdk_artifacts(result, extract_dir)
        if not content:
            content = MinerUClient.read_markdown(str(extract_dir))

        if not content:
            return ParseResult(
                task_id=task_id,
                state=MinerUClient.STATE_FAILED,
                zip_url=zip_url,
                zip_path="",
                extract_dir=str(extract_dir),
                error_msg="MinerU Open SDK completed but no Markdown content was produced",
            )

        return ParseResult(
            task_id=task_id,
            state=state,
            zip_url=zip_url,
            zip_path="",
            extract_dir=str(extract_dir),
            content=content,
        )

    def _save_sdk_artifacts(self, result: Any, extract_dir: Path) -> None:
        try:
            result.save_all(str(extract_dir))
        except Exception as exc:
            (extract_dir / "open_sdk_save_all_error.txt").write_text(str(exc), encoding="utf-8")

        markdown = getattr(result, "markdown", None)
        if markdown:
            (extract_dir / "full.md").write_text(markdown, encoding="utf-8")

        for attr, filename, write_binary in (
            ("html", "result.html", False),
            ("latex", "result.tex", False),
            ("docx", "result.docx", True),
        ):
            value = getattr(result, attr, None)
            if value is None:
                continue
            target = extract_dir / filename
            if write_binary:
                target.write_bytes(value)
            else:
                target.write_text(value, encoding="utf-8")

        self._write_debug_metadata(result, extract_dir)

    def _write_debug_metadata(self, result: Any, extract_dir: Path) -> None:
        payload = self._json_safe_result(result)
        (extract_dir / "open_sdk_result.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _progress_payload(self, result: Any) -> Dict[str, Any]:
        progress = getattr(result, "progress", None)
        payload: Dict[str, Any] = {
            "state": getattr(result, "state", "unknown"),
            "task_id": getattr(result, "task_id", ""),
            "err_msg": getattr(result, "error", None),
        }
        if progress:
            payload["extract_progress"] = {
                "extracted_pages": getattr(progress, "extracted_pages", 0),
                "total_pages": getattr(progress, "total_pages", 0),
                "start_time": getattr(progress, "start_time", ""),
            }
        return payload

    def _json_safe_result(self, result: Any) -> Dict[str, Any]:
        if is_dataclass(result):
            raw = asdict(result)
        elif hasattr(result, "__dict__"):
            raw = dict(result.__dict__)
        else:
            raw = {"repr": repr(result)}

        def scrub(value: Any) -> Any:
            if isinstance(value, bytes):
                return f"<bytes:{len(value)}>"
            if isinstance(value, dict):
                return {str(k): scrub(v) for k, v in value.items() if not str(k).startswith("_")}
            if isinstance(value, list):
                return [scrub(v) for v in value]
            if is_dataclass(value):
                return scrub(asdict(value))
            return value

        return scrub(raw)

    @staticmethod
    def _normalize_model(model_version: str) -> str:
        if model_version == MinerUClient.MODEL_HTML:
            return "html"
        return model_version


class MinerUProviderFactory:
    """Build configured MinerU providers."""

    SUPPORTED_MODES = {"open_sdk"}

    @classmethod
    def create(cls, config: MinerUConfig) -> MinerUProvider:
        mode = (config.provider_mode or "open_sdk").strip().lower()
        if mode == "open_sdk":
            return OpenSdkMinerUProvider(config)
        raise MinerUProviderError(
            f"Unsupported MinerU provider mode: {config.provider_mode}. "
            f"Supported modes: {', '.join(sorted(cls.SUPPORTED_MODES))}"
        )
