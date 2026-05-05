## ADDED Requirements

### Requirement: Profile objects are stored through StorageProvider
The system SHALL use StorageProvider for profile YAML and metadata persistence in addition to task artifact persistence.

#### Scenario: Local provider stores profiles
- **WHEN** `STORAGE_PROVIDER=local` and a profile is saved
- **THEN** profile YAML and metadata SHALL be persisted through the local storage provider

#### Scenario: MinIO provider stores profiles
- **WHEN** `STORAGE_PROVIDER=minio` and a profile is saved
- **THEN** profile YAML and metadata SHALL be persisted through the MinIO storage provider

#### Scenario: Profile keys are user-scoped
- **WHEN** a profile object key is generated
- **THEN** the key SHALL include the resolved user ID namespace before the profile ID
