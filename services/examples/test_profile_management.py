from fastapi.testclient import TestClient
import pytest

from services.api import server
from services.profiles.manager import (
    ADMIN_USER_ID,
    ProfileConflictError,
    ProfileCreateRequest,
    ProfileError,
    ProfileManager,
    ProfileUpdateRequest,
    RedisProfileStateStore,
)
from services.storage.local import LocalStorageProvider


VALID_PROFILE_YAML = "description: primary profile\n"
UPDATED_PROFILE_YAML = "description: updated profile\nmineru_model: pipeline\n"
INVALID_YAML = "description: [\n"
INVALID_CONFIG_YAML = "unknown_field: true\n"


class FakeRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def delete(self, key):
        self.values.pop(key, None)


def build_manager(tmp_path, seed_dir=None):
    storage = LocalStorageProvider(root_dir=str(tmp_path / "storage"))
    redis = FakeRedis()
    manager = ProfileManager(
        storage_provider=storage,
        active_state_store=RedisProfileStateStore(redis),
        seed_dir=seed_dir or (tmp_path / "seed"),
        enable_seed_import=True,
    )
    return manager, redis


def test_profile_manager_crud_and_activation(tmp_path):
    manager, _ = build_manager(tmp_path)

    detail = manager.create_profile(
        ADMIN_USER_ID,
        ProfileCreateRequest(
            content=VALID_PROFILE_YAML,
            filename="../main.yaml",
        ),
    )
    assert detail.profile_id == "main"
    assert detail.filename == "main.yaml"

    current_config, current_id = manager.get_current_config(ADMIN_USER_ID)
    assert current_id == "main"
    assert current_config.mineru_model == "vlm"

    state = manager.activate_profile(ADMIN_USER_ID, "main")
    assert state.current_profile_id == "main"
    assert manager.get_active_profile_id(ADMIN_USER_ID) == "main"

    updated = manager.update_profile(
        ADMIN_USER_ID,
        "main",
        ProfileUpdateRequest(content=UPDATED_PROFILE_YAML),
    )
    assert updated.config["mineru_model"] == "pipeline"
    assert manager.storage.list_keys("profiles/admin/main/versions")

    copied = manager.copy_profile(ADMIN_USER_ID, "main", "secondary.yaml")
    assert copied.profile_id == "secondary"

    with pytest.raises(ProfileConflictError):
        manager.delete_profile(ADMIN_USER_ID, "main")

    manager.activate_profile(ADMIN_USER_ID, "secondary")
    manager.delete_profile(ADMIN_USER_ID, "main")

    remaining = {item.profile_id for item in manager.list_profiles(ADMIN_USER_ID)}
    assert remaining == {"secondary"}


def test_profile_manager_validation_and_conflicts(tmp_path):
    manager, _ = build_manager(tmp_path)

    with pytest.raises(ProfileError, match="YAML format error"):
        manager.create_profile(
            ADMIN_USER_ID,
            ProfileCreateRequest(content=INVALID_YAML, filename="broken.yaml"),
        )

    with pytest.raises(ProfileError, match="validation failed"):
        manager.create_profile(
            ADMIN_USER_ID,
            ProfileCreateRequest(content=INVALID_CONFIG_YAML, filename="invalid.yaml"),
        )

    manager.create_profile(
        ADMIN_USER_ID,
        ProfileCreateRequest(content=VALID_PROFILE_YAML, filename="duplicate.yaml"),
    )

    with pytest.raises(ProfileConflictError):
        manager.create_profile(
            ADMIN_USER_ID,
            ProfileCreateRequest(content=VALID_PROFILE_YAML, filename="duplicate.yaml"),
        )


def test_profile_manager_seed_import_uses_local_profiles(tmp_path):
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "seed_profile.yaml").write_text(VALID_PROFILE_YAML, encoding="utf-8")
    (seed_dir / ".current.yaml").write_text("profile_file: seed_profile.yaml\n", encoding="utf-8")

    manager, _ = build_manager(tmp_path, seed_dir=seed_dir)
    profiles = manager.list_profiles(ADMIN_USER_ID)

    assert [item.profile_id for item in profiles] == ["seed_profile"]
    assert manager.get_active_profile_id(ADMIN_USER_ID) == "seed_profile"


def test_profile_current_route_prefers_static_handler(monkeypatch, tmp_path):
    manager, _ = build_manager(tmp_path)

    monkeypatch.setattr(server, "get_profile_manager", lambda: manager)
    monkeypatch.setattr(server, "get_current_user_id", lambda: ADMIN_USER_ID)

    client = TestClient(server.app)

    empty_response = client.get("/api/v1/profiles/current")
    assert empty_response.status_code == 200
    assert empty_response.json()["source"] == "default"

    create_response = client.post(
        "/api/v1/profiles",
        json={"content": VALID_PROFILE_YAML, "filename": "api-profile.yaml"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["profile_id"] == "api-profile"

    current_response = client.get("/api/v1/profiles/current")
    assert current_response.status_code == 200
    assert current_response.json()["source"] == "api-profile"
