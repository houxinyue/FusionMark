## Why

PDF preview displays incorrect orientation due to PDF.js rendering configuration not checking original PDF direction metadata. This affects user experience when viewing uploaded documents.

## What Changes

- Fix PDF.js rendering configuration to detect and correct PDF orientation
- Add PDF direction metadata checking before rendering
- Update frontend PDF preview component

## Capabilities

### New Capabilities
- `pdf-rendering`: PDF preview rendering with orientation correction

### Modified Capabilities
- None

## Impact

- Frontend PDF preview component (`frontend/src/`)
- No API changes
- No backend changes
