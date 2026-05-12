"""FastAPI routes for Profile Config Copilot."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.profiles import get_current_user_id, get_profile_manager

from .draft_generator import ProfileDraftGenerator
from .draft_validator import ProfileDraftValidator
from .service import ProfileCopilotService
from .session_store import InMemoryCopilotSessionStore


class CopilotMessagePayload(BaseModel):
    message: str = Field(..., min_length=1)


class CopilotValidatePayload(BaseModel):
    draft_yaml: Optional[str] = None


router = APIRouter(prefix="/api/v1/profile-copilot", tags=["profile-copilot"])
_profile_copilot_service: ProfileCopilotService | None = None


def get_profile_copilot_service() -> ProfileCopilotService:
    global _profile_copilot_service
    if _profile_copilot_service is None:
        _profile_copilot_service = ProfileCopilotService(
            profile_manager=get_profile_manager(),
            session_store=InMemoryCopilotSessionStore(),
            draft_generator=ProfileDraftGenerator(),
            validator=ProfileDraftValidator(),
        )
    return _profile_copilot_service


def reset_profile_copilot_service() -> None:
    global _profile_copilot_service
    _profile_copilot_service = None


@router.post("/sessions")
async def create_copilot_session():
    return get_profile_copilot_service().create_session(get_current_user_id())


@router.get("/sessions/{session_id}")
async def get_copilot_session(session_id: str):
    try:
        return get_profile_copilot_service().get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/messages")
async def send_copilot_message(session_id: str, payload: CopilotMessagePayload):
    try:
        return get_profile_copilot_service().process_message(
            session_id=session_id,
            user_id=get_current_user_id(),
            message=payload.message,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/validate")
async def validate_copilot_draft(session_id: str, payload: CopilotValidatePayload):
    try:
        return get_profile_copilot_service().validate_draft(
            session_id=session_id,
            user_id=get_current_user_id(),
            draft_yaml=payload.draft_yaml,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

