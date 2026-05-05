"""Storage-backed profile manager.

Profiles are YAML configuration files owned by a user namespace. The first
runtime user is the reserved ``admin`` user; future auth can replace the user
resolver without changing storage keys.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from services.core.full_pipeline import FullPipelineConfig
from services.storage import StorageProvider, get_storage_provider

ADMIN_USER_ID = "admin"
PROFILE_CONTENT_TYPE = "application/yaml"
PROFILE_META_CONTENT_TYPE = "application/json"
PROFILE_STATE_PREFIX = "user"
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class ProfileError(ValueError):
    """Base profile error that can be mapped to an API response."""


class ProfileNotFoundError(ProfileError):
    """Raised when a profile does not exist."""


class ProfileConflictError(ProfileError):
    """Raised when a profile operation conflicts with existing state."""


@dataclass
class ProfileMetadata:
    profile_id: str
    user_id: str
    filename: str
    display_name: str
    description: Optional[str]
    object_key: str
    meta_key: str
    size: int
    version: int
    created_at: str
    updated_at: str


@dataclass
class ProfileInfo:
    profile_id: str
    name: str
    filename: str
    display_name: str
    description: Optional[str]
    size: int
    created_at: str
    updated_at: str
    is_current: bool = False


@dataclass
class ProfileDetail(ProfileInfo):
    content: str = ""
    config: Optional[Dict[str, Any]] = None


@dataclass
class ProfileActiveState:
    current_profile_id: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ProfileCreateRequest:
    content: str
    filename: Optional[str] = None
    profile_id: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    set_as_current: bool = False
    overwrite: bool = False


@dataclass
class ProfileUpdateRequest:
    content: str
    filename: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    set_as_current: bool = False


def get_current_user_id() -> str:
    """Return the reserved user ID until authentication is introduced."""
    return ADMIN_USER_ID


def _now() -> str:
    return datetime.now().isoformat()


def _decode_text(data: bytes) -> str:
    return data.decode("utf-8")


def _encode_text(text: str) -> bytes:
    return text.encode("utf-8")


def _safe_component(value: str, fallback: str) -> str:
    raw = Path(value or fallback).name.strip()
    cleaned = SAFE_NAME_RE.sub("_", raw).strip("._-")
    return cleaned or fallback


def normalize_profile_id(value: Optional[str], filename: Optional[str] = None) -> str:
    source = value or Path(filename or "").stem or f"profile-{uuid.uuid4().hex[:8]}"
    return _safe_component(source, "profile")


def normalize_filename(value: Optional[str], profile_id: str) -> str:
    filename = _safe_component(value or profile_id, profile_id)
    suffix = Path(filename).suffix.lower()
    if suffix not in (".yaml", ".yml"):
        filename = f"{Path(filename).stem or profile_id}.yaml"
    return filename


def extract_description(config_data: Dict[str, Any], explicit: Optional[str]) -> Optional[str]:
    if explicit is not None:
        return explicit
    description = config_data.get("description")
    return description if isinstance(description, str) else None


class RedisProfileStateStore:
    """Small Redis-backed active-profile state store."""

    def __init__(self, redis_client: Any):
        self.redis = redis_client

    def _key(self, user_id: str) -> str:
        return f"{PROFILE_STATE_PREFIX}:{user_id}:profiles"

    def get(self, user_id: str) -> ProfileActiveState:
        data = self.redis.get(self._key(user_id))
        if not data:
            return ProfileActiveState()
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return ProfileActiveState()
        return ProfileActiveState(
            current_profile_id=payload.get("current_profile_id"),
            updated_at=payload.get("updated_at"),
        )

    def set_current(self, user_id: str, profile_id: str) -> ProfileActiveState:
        state = ProfileActiveState(current_profile_id=profile_id, updated_at=_now())
        self.redis.set(self._key(user_id), json.dumps(asdict(state), ensure_ascii=False))
        return state

    def clear(self, user_id: str) -> None:
        self.redis.delete(self._key(user_id))


class ProfileManager:
    """Manage user-scoped YAML profiles through StorageProvider."""

    def __init__(
        self,
        storage_provider: StorageProvider,
        active_state_store: Optional[RedisProfileStateStore] = None,
        seed_dir: Optional[Path] = None,
        enable_seed_import: bool = True,
    ):
        self.storage = storage_provider
        self.active_state_store = active_state_store
        self.seed_dir = seed_dir or Path(__file__).parent
        self.enable_seed_import = enable_seed_import

    def list_profiles(self, user_id: str) -> List[ProfileInfo]:
        self.ensure_seeded(user_id)
        current_id = self.get_active_profile_id(user_id)
        infos: List[ProfileInfo] = []
        for meta in self._list_metadata(user_id):
            infos.append(self._to_info(meta, current_id))
        infos.sort(key=lambda item: item.updated_at, reverse=True)
        return infos

    def get_profile(self, user_id: str, profile_id: str) -> ProfileDetail:
        self.ensure_seeded(user_id)
        normalized_id = normalize_profile_id(profile_id)
        meta = self._read_metadata(user_id, normalized_id)
        content = self._read_yaml(meta.object_key)
        config = self._validate_yaml(content)[1].to_dict()
        current_id = self.get_active_profile_id(user_id)
        info = self._to_info(meta, current_id)
        return ProfileDetail(**asdict(info), content=content, config=config)

    def create_profile(self, user_id: str, request: ProfileCreateRequest) -> ProfileDetail:
        config_data, config = self._validate_yaml(request.content)
        profile_id = normalize_profile_id(request.profile_id, request.filename)
        filename = normalize_filename(request.filename, profile_id)
        display_name = request.display_name or Path(filename).stem
        description = extract_description(config_data, request.description)

        if self._profile_exists(user_id, profile_id) and not request.overwrite:
            raise ProfileConflictError(f"Profile '{profile_id}' already exists")

        if self._profile_exists(user_id, profile_id) and request.overwrite:
            self._backup_current_yaml(user_id, profile_id)
            version = self._read_metadata(user_id, profile_id).version + 1
            created_at = self._read_metadata(user_id, profile_id).created_at
        else:
            version = 1
            created_at = _now()

        meta = self._build_metadata(
            user_id=user_id,
            profile_id=profile_id,
            filename=filename,
            display_name=display_name,
            description=description,
            content=request.content,
            version=version,
            created_at=created_at,
        )
        self._write_profile(meta, request.content)
        if request.set_as_current:
            self.activate_profile(user_id, profile_id)
        return self.get_profile(user_id, profile_id)

    def update_profile(self, user_id: str, profile_id: str, request: ProfileUpdateRequest) -> ProfileDetail:
        self._validate_yaml(request.content)
        normalized_id = normalize_profile_id(profile_id)
        existing = self._read_metadata(user_id, normalized_id)
        self._backup_current_yaml(user_id, normalized_id)
        config_data, _ = self._validate_yaml(request.content)

        meta = self._build_metadata(
            user_id=user_id,
            profile_id=normalized_id,
            filename=normalize_filename(request.filename or existing.filename, normalized_id),
            display_name=request.display_name or existing.display_name,
            description=extract_description(config_data, request.description if request.description is not None else existing.description),
            content=request.content,
            version=existing.version + 1,
            created_at=existing.created_at,
        )
        self._write_profile(meta, request.content)
        if request.set_as_current:
            self.activate_profile(user_id, normalized_id)
        return self.get_profile(user_id, normalized_id)

    def copy_profile(self, user_id: str, source_profile_id: str, target_filename: str) -> ProfileDetail:
        source = self.get_profile(user_id, source_profile_id)
        target_id = normalize_profile_id(None, target_filename)
        return self.create_profile(
            user_id,
            ProfileCreateRequest(
                content=source.content,
                filename=target_filename,
                profile_id=target_id,
                display_name=Path(target_filename).stem,
                description=source.description,
                set_as_current=False,
                overwrite=False,
            ),
        )

    def delete_profile(self, user_id: str, profile_id: str) -> None:
        normalized_id = normalize_profile_id(profile_id)
        active_id = self.get_active_profile_id(user_id)
        if active_id == normalized_id:
            raise ProfileConflictError("Cannot delete the active profile. Activate another profile first.")

        meta = self._read_metadata(user_id, normalized_id)
        keys = self.storage.list_keys(self._profile_prefix(user_id, normalized_id))
        for key in keys:
            self.storage.delete(key)
        self.storage.delete(meta.object_key)
        self.storage.delete(meta.meta_key)

    def activate_profile(self, user_id: str, profile_id: str) -> ProfileActiveState:
        normalized_id = normalize_profile_id(profile_id)
        profile = self.get_profile(user_id, normalized_id)
        self._validate_yaml(profile.content)
        if self.active_state_store is None:
            raise ProfileError("Redis active profile store is not configured")
        return self.active_state_store.set_current(user_id, normalized_id)

    def get_active_profile_id(self, user_id: str) -> Optional[str]:
        if self.active_state_store is None:
            return None
        try:
            return self.active_state_store.get(user_id).current_profile_id
        except Exception:
            return None

    def get_current_config(self, user_id: str) -> Tuple[FullPipelineConfig, Optional[str]]:
        self.ensure_seeded(user_id)
        active_id = self.get_active_profile_id(user_id)
        if active_id:
            try:
                detail = self.get_profile(user_id, active_id)
                return FullPipelineConfig.from_dict(yaml.safe_load(detail.content) or {}), active_id
            except Exception as exc:
                print(f"[!] Failed to load active profile '{active_id}': {exc}")

        profiles = self.list_profiles(user_id)
        if profiles:
            try:
                detail = self.get_profile(user_id, profiles[0].profile_id)
                return FullPipelineConfig.from_dict(yaml.safe_load(detail.content) or {}), profiles[0].profile_id
            except Exception as exc:
                print(f"[!] Failed to load fallback profile '{profiles[0].profile_id}': {exc}")

        return FullPipelineConfig(), None

    def ensure_seeded(self, user_id: str) -> None:
        if not self.enable_seed_import:
            return
        if self.storage.list_keys(self._user_prefix(user_id)):
            return
        if not self.seed_dir.exists():
            return

        current_filename = self._read_local_current_filename()
        imported_ids: Dict[str, str] = {}
        for path in sorted(self.seed_dir.glob("*.yml")) + sorted(self.seed_dir.glob("*.yaml")):
            if path.name == ".current.yaml":
                continue
            try:
                content = path.read_text(encoding="utf-8")
                self._validate_yaml(content)
            except Exception as exc:
                print(f"[!] Skip invalid seed profile '{path.name}': {exc}")
                continue

            profile_id = normalize_profile_id(None, path.name)
            try:
                self.create_profile(
                    user_id,
                    ProfileCreateRequest(
                        content=content,
                        filename=path.name,
                        profile_id=profile_id,
                        display_name=path.stem,
                        overwrite=False,
                    ),
                )
                imported_ids[path.name] = profile_id
            except ProfileConflictError:
                imported_ids[path.name] = profile_id

        if current_filename and current_filename in imported_ids and self.active_state_store is not None:
            try:
                self.active_state_store.set_current(user_id, imported_ids[current_filename])
            except Exception as exc:
                print(f"[!] Failed to seed active profile state: {exc}")

    def _validate_yaml(self, content: str) -> Tuple[Dict[str, Any], FullPipelineConfig]:
        if not content or not content.strip():
            raise ProfileError("YAML content cannot be empty")
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise ProfileError(f"YAML format error: {exc}") from exc
        if not isinstance(data, dict):
            raise ProfileError("YAML root must be an object")
        try:
            config = FullPipelineConfig.from_dict(data)
        except Exception as exc:
            raise ProfileError(f"Profile config validation failed: {exc}") from exc
        return data, config

    def _read_local_current_filename(self) -> Optional[str]:
        current_file = self.seed_dir / ".current.yaml"
        if not current_file.exists():
            return None
        try:
            current = yaml.safe_load(current_file.read_text(encoding="utf-8")) or {}
        except Exception:
            return None
        profile_file = current.get("profile_file")
        return profile_file if isinstance(profile_file, str) else None

    def _build_metadata(
        self,
        user_id: str,
        profile_id: str,
        filename: str,
        display_name: str,
        description: Optional[str],
        content: str,
        version: int,
        created_at: str,
    ) -> ProfileMetadata:
        now = _now()
        return ProfileMetadata(
            profile_id=profile_id,
            user_id=user_id,
            filename=filename,
            display_name=display_name,
            description=description,
            object_key=self._profile_yaml_key(user_id, profile_id),
            meta_key=self._profile_meta_key(user_id, profile_id),
            size=len(_encode_text(content)),
            version=version,
            created_at=created_at,
            updated_at=now,
        )

    def _write_profile(self, meta: ProfileMetadata, content: str) -> None:
        self.storage.save_bytes(meta.object_key, _encode_text(content), content_type=PROFILE_CONTENT_TYPE)
        self.storage.save_bytes(
            meta.meta_key,
            json.dumps(asdict(meta), ensure_ascii=False, indent=2).encode("utf-8"),
            content_type=PROFILE_META_CONTENT_TYPE,
        )

    def _backup_current_yaml(self, user_id: str, profile_id: str) -> None:
        key = self._profile_yaml_key(user_id, profile_id)
        data = self.storage.read_bytes(key)
        if data is None:
            return
        backup_key = f"{self._profile_prefix(user_id, profile_id)}/versions/{datetime.now().strftime('%Y%m%d%H%M%S')}.yaml"
        self.storage.save_bytes(backup_key, data, content_type=PROFILE_CONTENT_TYPE)

    def _read_metadata(self, user_id: str, profile_id: str) -> ProfileMetadata:
        key = self._profile_meta_key(user_id, profile_id)
        data = self.storage.read_bytes(key)
        if data is None:
            raise ProfileNotFoundError(f"Profile '{profile_id}' not found")
        payload = json.loads(_decode_text(data))
        return ProfileMetadata(**payload)

    def _read_yaml(self, key: str) -> str:
        data = self.storage.read_bytes(key)
        if data is None:
            raise ProfileNotFoundError("Profile YAML content not found")
        return _decode_text(data)

    def _list_metadata(self, user_id: str) -> List[ProfileMetadata]:
        metadata: List[ProfileMetadata] = []
        for key in self.storage.list_keys(self._user_prefix(user_id)):
            if not key.endswith("/meta.json"):
                continue
            data = self.storage.read_bytes(key)
            if data is None:
                continue
            try:
                metadata.append(ProfileMetadata(**json.loads(_decode_text(data))))
            except Exception as exc:
                print(f"[!] Skip invalid profile metadata '{key}': {exc}")
        return metadata

    def _profile_exists(self, user_id: str, profile_id: str) -> bool:
        return self.storage.exists(self._profile_meta_key(user_id, profile_id))

    def _to_info(self, meta: ProfileMetadata, current_id: Optional[str]) -> ProfileInfo:
        return ProfileInfo(
            profile_id=meta.profile_id,
            name=meta.profile_id,
            filename=meta.filename,
            display_name=meta.display_name,
            description=meta.description,
            size=meta.size,
            created_at=meta.created_at,
            updated_at=meta.updated_at,
            is_current=meta.profile_id == current_id,
        )

    @staticmethod
    def _user_prefix(user_id: str) -> str:
        return f"profiles/{_safe_component(user_id, ADMIN_USER_ID)}"

    @classmethod
    def _profile_prefix(cls, user_id: str, profile_id: str) -> str:
        return f"{cls._user_prefix(user_id)}/{normalize_profile_id(profile_id)}"

    @classmethod
    def _profile_yaml_key(cls, user_id: str, profile_id: str) -> str:
        return f"{cls._profile_prefix(user_id, profile_id)}/profile.yaml"

    @classmethod
    def _profile_meta_key(cls, user_id: str, profile_id: str) -> str:
        return f"{cls._profile_prefix(user_id, profile_id)}/meta.json"


_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Return the process-wide profile manager."""
    global _profile_manager
    if _profile_manager is None:
        try:
            from services.api.progress_store import get_progress_store

            active_store = RedisProfileStateStore(get_progress_store().redis)
        except Exception as exc:
            print(f"[!] Redis profile active state unavailable: {exc}")
            active_store = None

        _profile_manager = ProfileManager(
            storage_provider=get_storage_provider(),
            active_state_store=active_store,
            seed_dir=Path(__file__).parent,
        )
    return _profile_manager


def reset_profile_manager() -> None:
    """Reset global profile manager for tests."""
    global _profile_manager
    _profile_manager = None
