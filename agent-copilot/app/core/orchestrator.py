from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OrchestrationResult:
    session_id: str
    status: str
