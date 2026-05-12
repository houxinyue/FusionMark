"""Profile Config Copilot orchestration service."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from services.profiles import ProfileManager

from .draft_generator import DraftGenerationError, ProfileDraftGenerator
from .draft_validator import ProfileDraftValidator
from .guardrails import CopilotGuardrails
from .profile_context import ProfileContextProvider
from .schemas import CopilotMessage, DraftGenerationRequest
from .session_store import CopilotSessionStore


class ProfileCopilotService:
    """Coordinate Profile YAML draft sessions."""

    def __init__(
        self,
        profile_manager: ProfileManager,
        session_store: CopilotSessionStore,
        draft_generator: ProfileDraftGenerator,
        validator: ProfileDraftValidator | None = None,
        guardrails: CopilotGuardrails | None = None,
        context_provider: ProfileContextProvider | None = None,
    ) -> None:
        self.profile_manager = profile_manager
        self.session_store = session_store
        self.draft_generator = draft_generator
        self.validator = validator or ProfileDraftValidator()
        self.guardrails = guardrails or CopilotGuardrails()
        self.context_provider = context_provider or ProfileContextProvider(profile_manager)

    def create_session(self, user_id: str) -> Dict[str, Any]:
        session = self.session_store.create(user_id)
        return self._serialize_session(session)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self._serialize_session(self.session_store.get(session_id))

    def process_message(self, session_id: str, user_id: str, message: str) -> Dict[str, Any]:
        session = self.session_store.get(session_id)
        if session.user_id != user_id:
            raise KeyError(f"Copilot session '{session_id}' not found")

        session.messages.append(CopilotMessage(role="user", content=message))
        guardrail = self.guardrails.check(message)
        if not guardrail.allowed:
            session.messages.append(CopilotMessage(role="assistant", content=guardrail.reason))
            self.session_store.save(session)
            response = self._serialize_session(session)
            response.update({"assistant_message": guardrail.reason, "rejected": True})
            return response

        referenced_profiles = self.context_provider.retrieve(user_id, message)
        session.referenced_profiles = referenced_profiles

        try:
            generation = self.draft_generator.generate(
                DraftGenerationRequest(
                    user_message=message,
                    current_draft_yaml=session.current_draft_yaml,
                    conversation=session.messages,
                    referenced_profiles=referenced_profiles,
                )
            )
        except DraftGenerationError as exc:
            assistant_message = str(exc)
            session.messages.append(CopilotMessage(role="assistant", content=assistant_message))
            self.session_store.save(session)
            response = self._serialize_session(session)
            response.update({"assistant_message": assistant_message, "rejected": False, "generation_error": True})
            return response

        validation = self.validator.validate(generation.draft_yaml)
        session.current_draft_yaml = generation.draft_yaml
        session.validation = validation
        session.messages.append(CopilotMessage(role="assistant", content=generation.assistant_message))
        self.session_store.save(session)

        response = self._serialize_session(session)
        response.update({"assistant_message": generation.assistant_message, "rejected": False})
        return response

    def validate_draft(self, session_id: str, user_id: str, draft_yaml: str | None = None) -> Dict[str, Any]:
        session = self.session_store.get(session_id)
        if session.user_id != user_id:
            raise KeyError(f"Copilot session '{session_id}' not found")
        content = draft_yaml if draft_yaml is not None else session.current_draft_yaml
        session.validation = self.validator.validate(content)
        if draft_yaml is not None:
            session.current_draft_yaml = draft_yaml
        self.session_store.save(session)
        return self._serialize_session(session)

    def _serialize_session(self, session) -> Dict[str, Any]:
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "messages": [asdict(message) for message in session.messages],
            "draft_yaml": session.current_draft_yaml,
            "validation": asdict(session.validation),
            "referenced_profiles": [asdict(profile) for profile in session.referenced_profiles],
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

