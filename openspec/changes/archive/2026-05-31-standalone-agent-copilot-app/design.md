## Overview

This change establishes a standalone application root for the copilot so future work can land in a dedicated boundary instead of scattering across the main service.

## Proposed Layout

```text
agent-copilot/
├── README.md
├── pyproject.toml
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── agent/
│   ├── storage/
│   ├── models/
│   ├── schemas/
│   ├── config/
│   ├── prompts/
│   └── utils/
├── tests/
└── scripts/
```

## Boundary Rules

- `app/api/` only exposes transport handlers.
- `app/core/` owns orchestration and state flow.
- `app/agent/` owns prompt-facing reasoning pieces.
- `app/storage/` owns session and archive access abstractions.
- `app/prompts/` stores prompt assets as files, not inline code.

## Stage Breakdown

### Stage 1: Root scaffold

Create the standalone directory, startup entrypoint, and basic package structure.

### Stage 2: Core service skeleton

Add session model, orchestration shell, and storage interfaces without binding to Redis or MinIO.

### Stage 3: Runtime integration

Wire the session store, checkpoint handling, and validation flow.

### Stage 4: API and UI integration

Expose HTTP routes and connect the frontend assistant panel.

## Implementation Notes

- Keep the module runnable in isolation.
- Keep existing profile editing and activation controls untouched.
- Prefer injectable interfaces so storage and model clients can be swapped later.
- Keep the first phase deterministic and minimal.
