## Context

The backend currently has profile endpoints in `services/api/server.py`, but profile state is still tied to local files under `services/profiles/` and `.current.yaml`. The project now has a StorageProvider abstraction for local and MinIO object storage, plus Redis-backed task state. Profile YAML management should use those same infrastructure boundaries.

The first user identity is reserved as `admin`. This is not an authentication implementation; it is a stable ownership boundary so future permissions can replace the user resolver without changing storage keys or API contracts.

## Goals / Non-Goals

**Goals:**
- Persist profile YAML and profile metadata through StorageProvider.
- Store active profile selection in Redis using a user-scoped key.
- Default all profile operations to the reserved `admin` user.
- Provide backend CRUD APIs for online YAML editing and upload.
- Update pipeline config resolution so task processing uses the Redis active profile pointer and StorageProvider content.
- Build a usable frontend configuration management page.
- Keep the implementation plugin-style: profile logic lives in a dedicated manager/service rather than in route handlers.

**Non-Goals:**
- Add login, JWT, RBAC, or multi-user UI in this change.
- Build a visual form editor for every YAML field.
- Add collaborative editing or conflict-free multi-editor semantics.
- Keep `services/profiles/.current.yaml` as runtime state.
- Migrate historical profile versions beyond first-run/import seed behavior.

## Decisions

### Decision 1: Use `admin` through a user resolver

Create a small resolver boundary, for example `get_current_user_id() -> "admin"`, and require profile manager methods to receive `user_id`.

**Rationale**: Future permission work can replace the resolver with auth context while preserving storage layout and API behavior.

**Alternative considered**: Hardcode `admin` in each route. This is simpler initially but spreads future auth migration work across the API.

### Decision 2: Store profile files in StorageProvider

Use object keys like:

```text
profiles/{user_id}/{profile_id}/profile.yaml
profiles/{user_id}/{profile_id}/meta.json
profiles/{user_id}/{profile_id}/versions/{timestamp}.yaml
```

**Rationale**: This reuses the existing local/MinIO provider switch and removes local project directories from runtime profile state.

**Alternative considered**: Store YAML content in Redis. Redis is better for current pointers and fast state, but not ideal as the durable source of profile files, large YAML content, or version history.

### Decision 3: Store active profile in Redis

Use a user-scoped Redis value such as:

```text
user:admin:profiles
```

with JSON content:

```json
{
  "current_profile_id": "full_pipeline_config",
  "updated_at": "2026-05-05T00:00:00"
}
```

**Rationale**: Active profile selection is mutable runtime state and should not require rewriting a YAML file in object storage.

**Alternative considered**: Store `current.json` in StorageProvider. That is durable, but less suitable for frequently updated runtime state and less aligned with the existing Redis state model.

### Decision 4: Preserve raw YAML text on create/update/upload

Validate YAML by parsing and constructing `FullPipelineConfig`, but store the submitted raw YAML bytes.

**Rationale**: Users editing YAML expect comments, ordering, anchors, and formatting to survive. `yaml.dump` would normalize output and lose that editing context.

**Alternative considered**: Re-serialize all profiles from Python dicts. That gives consistent formatting but degrades online editing.

### Decision 5: Separate profile identity from filename

Use `profile_id` as the stable storage identity. Keep `filename`, `display_name`, and `description` in metadata.

**Rationale**: A profile can be renamed or downloaded with a friendly filename without changing the storage namespace or current pointer.

**Alternative considered**: Use filename as the primary key. This creates conflicts around rename, duplicate uploads, and future permissions.

### Decision 6: Lazy seed from local profiles only when storage is empty

On first access, the manager can import `services/profiles/*.yaml` for `admin` when no storage-backed profiles exist. `.current.yaml` can be used only to initialize the Redis active pointer.

**Rationale**: Existing development profiles remain available without preserving local files as the runtime source of truth.

**Alternative considered**: Require a manual migration command before the feature works. That is cleaner operationally but slows local adoption.

## API Shape

Routes remain scoped to the current user implicitly:

```http
GET    /api/v1/profiles
GET    /api/v1/profiles/current
GET    /api/v1/profiles/{profile_id}
POST   /api/v1/profiles
PUT    /api/v1/profiles/{profile_id}
DELETE /api/v1/profiles/{profile_id}
POST   /api/v1/profiles/{profile_id}/activate
POST   /api/v1/profiles/{profile_id}/copy
POST   /api/v1/profiles/upload
GET    /api/v1/profiles/{profile_id}/download
GET    /api/v1/config/default
```

The frontend does not send `user_id` in the first version. The backend resolves it to `admin`.

## Frontend Shape

`ConfigView.vue` becomes a real workbench:

```text
Profile list        YAML editor                 Summary/actions
- current badge     - filename/display name     - validation status
- updated time      - raw YAML textarea/editor   - activate/save/copy
- size              - dirty state               - upload/download/delete
```

Start with Naive UI controls and a textarea editor. CodeMirror can be introduced later if YAML editing needs richer highlighting.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Existing code still reads `.current.yaml` | Route all config resolution through `ProfileManager.get_current_config(user_id)` |
| MinIO metadata tags are not enough for full profile metadata | Store `meta.json` as a normal object next to `profile.yaml` |
| Deleting the active profile leaves tasks without config | Reject deleting the active profile until another profile is activated |
| Redis loses active pointer | Fall back to first available profile or default config with a clear warning; do not mutate storage silently |
| Upload overwrites an existing profile unexpectedly | Require explicit `overwrite=true` or generate a unique `profile_id` |
| Raw YAML can include secrets | Do not log profile content; redact sensitive values in errors and documentation |

## Migration Plan

1. Add profile manager models and StorageProvider-backed persistence.
2. Add Redis active-profile state helpers with `admin` user resolver.
3. Implement lazy import from `services/profiles/*.yaml` when storage profiles are empty.
4. Replace local `.current.yaml` reads in API and task processing with profile manager resolution.
5. Extend profile APIs for CRUD/edit/upload/copy/download/activate.
6. Build the frontend configuration management UI.
7. Add backend tests for local provider, Redis active pointer, YAML validation, and delete protection.
8. Add frontend build/type validation.

## Open Questions

1. Should Redis active-profile state use the existing progress store abstraction or a small dedicated Redis helper?
2. Should first-run seed import be enabled by default in production, or controlled by an environment variable?
3. Should profile version backups be exposed in the UI now, or only written for future recovery?
