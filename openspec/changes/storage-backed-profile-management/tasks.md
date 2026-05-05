## 1. Backend Profile Domain

- [x] 1.1 Create profile domain models for profile metadata, detail responses, create/update payloads, and activation state
- [x] 1.2 Add a current-user resolver that returns reserved user ID `admin`
- [x] 1.3 Implement safe profile ID and filename normalization with path traversal protection
- [x] 1.4 Implement YAML validation that preserves raw YAML text while checking `FullPipelineConfig` compatibility

## 2. Storage and Redis Profile Manager

- [x] 2.1 Implement a StorageProvider-backed `ProfileManager` for list/read/create/update/copy/delete/upload/download operations
- [x] 2.2 Store profile YAML at `profiles/{user_id}/{profile_id}/profile.yaml`
- [x] 2.3 Store profile metadata at `profiles/{user_id}/{profile_id}/meta.json`
- [x] 2.4 Store profile version backups at `profiles/{user_id}/{profile_id}/versions/{timestamp}.yaml` before overwrites
- [x] 2.5 Store active profile state in Redis under a user-scoped key
- [x] 2.6 Reject deletion of the active profile unless the active profile is changed first
- [x] 2.7 Add optional first-run seed import from `services/profiles/*.yaml` into `profiles/admin/`

## 3. Backend API Integration

- [x] 3.1 Replace local profile helper logic in `services/api/server.py` with `ProfileManager`
- [x] 3.2 Add or update profile CRUD endpoints for list, current, read, create, update, copy, upload, download, delete, and activate
- [x] 3.3 Update activation to validate profile YAML, write Redis active state, and refresh `pipeline_service`
- [x] 3.4 Update task processing config resolution to use the storage-backed active profile instead of `.current.yaml`
- [x] 3.5 Preserve backward-compatible response fields where practical for existing frontend/API consumers
- [ ] 3.6 Update README/API documentation for storage-backed profile management

## 4. Frontend API and State

- [x] 4.1 Add `web-pc/src/types/profile.ts` with profile list/detail/request types
- [x] 4.2 Add `web-pc/src/api/profileApi.ts` for profile CRUD, upload, activate, download, and default config calls
- [x] 4.3 Add a Pinia profile store or equivalent view-local state for list, selected profile, dirty state, and loading/error handling

## 5. Frontend Configuration Page

- [x] 5.1 Replace `ConfigView.vue` placeholder with a profile management workbench
- [x] 5.2 Add profile list with active badge, metadata, refresh, activate, download, and delete actions
- [x] 5.3 Add YAML editor area for online editing and save validation feedback
- [x] 5.4 Add create/copy flow for new profiles
- [x] 5.5 Add YAML upload flow with overwrite handling and list refresh
- [x] 5.6 Add summary panel for profile status, filename, size, updated time, and validation messages
- [x] 5.7 Ensure responsive layout works for desktop and narrower screens

## 6. Validation

- [x] 6.1 Add backend tests for local StorageProvider profile CRUD
- [x] 6.2 Add backend tests for Redis active profile state and current config resolution
- [x] 6.3 Add backend tests for invalid YAML, invalid config shape, path traversal, duplicate profile, and active delete rejection
- [x] 6.4 Add backend tests for first-run seed import from local profiles
- [x] 6.5 Run `uv run pytest`
- [ ] 6.6 Run frontend build and type/lint checks according to `web-pc` scripts
- [ ] 6.7 Manually verify create/edit/upload/activate/delete/download in the config page
