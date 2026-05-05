## ADDED Requirements

### Requirement: User-scoped profile storage
The system SHALL store YAML profiles under a user-scoped namespace using the configured StorageProvider.

#### Scenario: Default admin user stores profile
- **WHEN** a profile is created before authentication exists
- **THEN** the system SHALL store the profile under the reserved `admin` user namespace

#### Scenario: Profile content is persisted through storage provider
- **WHEN** a profile YAML file is created, uploaded, or updated
- **THEN** the system SHALL persist the raw YAML content through StorageProvider

#### Scenario: Profile metadata is persisted with profile
- **WHEN** a profile is created, uploaded, or updated
- **THEN** the system SHALL persist metadata including profile ID, user ID, filename, timestamps, size, and description where available

### Requirement: Redis active profile pointer
The system SHALL store the active profile selection in Redis using a user-scoped key.

#### Scenario: Profile is activated
- **WHEN** a user activates a profile
- **THEN** the system SHALL validate the profile exists and can load as `FullPipelineConfig`
- **AND** the system SHALL store the active profile ID in Redis for that user

#### Scenario: Current profile is resolved
- **WHEN** task processing needs the current profile
- **THEN** the system SHALL read the user active profile ID from Redis and load the corresponding YAML from StorageProvider

#### Scenario: No active profile exists
- **WHEN** Redis has no active profile pointer for the user
- **THEN** the system SHALL fall back to the default `FullPipelineConfig` or a seeded profile without reading `.current.yaml` as runtime state

### Requirement: Profile CRUD API
The system SHALL expose APIs for listing, reading, creating, updating, copying, deleting, uploading, downloading, and activating profiles.

#### Scenario: List profiles
- **WHEN** a client requests `GET /api/v1/profiles`
- **THEN** the system SHALL return profiles owned by the resolved current user and mark the active profile

#### Scenario: Read profile content
- **WHEN** a client requests a specific profile
- **THEN** the system SHALL return metadata and raw YAML content for online editing

#### Scenario: Create profile from YAML text
- **WHEN** a client creates a profile with YAML content
- **THEN** the system SHALL validate YAML syntax and `FullPipelineConfig` compatibility before storing it

#### Scenario: Update profile from YAML text
- **WHEN** a client updates a profile with YAML content
- **THEN** the system SHALL validate the content and persist the raw YAML without reformatting it

#### Scenario: Upload profile file
- **WHEN** a client uploads a `.yaml` or `.yml` file
- **THEN** the system SHALL validate and store it as a user-scoped profile

#### Scenario: Delete active profile is rejected
- **WHEN** a client attempts to delete the currently active profile
- **THEN** the system SHALL reject the operation and instruct the client to activate another profile first

### Requirement: Local profile runtime dependency is removed
The system SHALL stop using `services/profiles/.current.yaml` and local profile files as runtime source of truth.

#### Scenario: Current profile is needed
- **WHEN** API task processing or pipeline service loading resolves configuration
- **THEN** the system SHALL use the storage-backed profile manager instead of reading `services/profiles/.current.yaml`

#### Scenario: Local profiles exist
- **WHEN** storage-backed profiles are empty and local seed YAML files exist
- **THEN** the system MAY import local YAML files into the `admin` storage namespace as seed data

### Requirement: Profile management frontend
The frontend SHALL provide a configuration management interface for storage-backed profiles.

#### Scenario: User edits profile online
- **WHEN** a user opens the configuration management page and selects a profile
- **THEN** the frontend SHALL show profile metadata and raw YAML content in an editable area

#### Scenario: User saves profile
- **WHEN** a user saves edited YAML
- **THEN** the frontend SHALL call the update API and show validation or save errors

#### Scenario: User uploads profile
- **WHEN** a user uploads a YAML file
- **THEN** the frontend SHALL call the upload API and refresh the profile list after success

#### Scenario: User activates profile
- **WHEN** a user activates a profile from the configuration page
- **THEN** the frontend SHALL update the active profile indicator after the backend confirms activation
