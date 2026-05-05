## Why

Profile YAML configuration is currently treated as local runtime state under `services/profiles/`. That blocks clean object-storage deployment, makes active profile state local to one process directory, and leaves no clean user boundary for future permissions.

We need storage-backed profile management where YAML files are persisted through the existing StorageProvider, active profile selection is stored in Redis by user, and the first user is reserved as `admin`.

## What Changes

- Add storage-backed profile CRUD for YAML configuration files.
- Store profile YAML and metadata through the configured StorageProvider instead of `services/profiles/` as runtime state.
- Store the active profile pointer in Redis under a user-scoped key for the reserved `admin` user.
- Add online create/edit/save, upload, download, copy, delete, activate, and current-profile APIs.
- Update task processing and pipeline service config loading to resolve the current profile through the new profile manager.
- Add a frontend configuration management page for listing, editing, uploading, activating, deleting, and downloading YAML profiles.
- Keep local `services/profiles/` only as an optional seed/migration source, not as the source of truth.
- **BREAKING**: Runtime profile state will no longer be read from `services/profiles/.current.yaml`.

## Capabilities

### New Capabilities
- `profile-management`: User-scoped YAML profile management backed by StorageProvider and Redis active-profile state.

### Modified Capabilities
- `artifact-storage`: Profile YAML files and metadata are additional storage-backed objects managed through the StorageProvider.

## Impact

- Backend API under `services/api/server.py`, with profile logic moved into a dedicated manager/service module.
- New profile domain models and storage key conventions under `services/profiles/` or an equivalent service package.
- Redis progress store or Redis client usage for `user:{user_id}:profiles` active-profile state.
- Existing config loading in `services/api/server.py` and `services/api/task_processor.py`.
- Existing StorageProvider implementations under `services/storage/`.
- Frontend `web-pc/src/views/ConfigView.vue`, plus new profile API/types/store/components as needed.
- README/API documentation and backend/frontend tests.
