from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class MessagePayload:
    role: str
    content: str


@dataclass
class SessionPayload:
    session_id: str
    user_id: str
    messages: List[MessagePayload]
