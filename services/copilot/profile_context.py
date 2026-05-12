"""Profile context retrieval for draft generation."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from services.profiles import ProfileManager

from .draft_validator import ProfileDraftValidator
from .schemas import CopilotReferencedProfile


class ProfileContextProvider:
    """Build lightweight context from existing profiles through ProfileManager."""

    def __init__(self, profile_manager: ProfileManager, max_profiles: int = 3) -> None:
        self.profile_manager = profile_manager
        self.max_profiles = max_profiles

    def retrieve(self, user_id: str, query: str) -> List[CopilotReferencedProfile]:
        candidates: List[CopilotReferencedProfile] = []
        query_terms = self._tokenize(query)

        for profile in self.profile_manager.list_profiles(user_id):
            try:
                detail = self.profile_manager.get_profile(user_id, profile.profile_id)
            except Exception:
                continue
            config_data = ProfileDraftValidator.parse_mapping(detail.content)
            summary = self._summarize_config(config_data)
            searchable = " ".join(
                item
                for item in [
                    detail.display_name,
                    detail.description or "",
                    summary,
                ]
                if item
            )
            score = self._score(searchable, query_terms)
            if score <= 0 and query_terms:
                continue
            candidates.append(
                CopilotReferencedProfile(
                    profile_id=detail.profile_id,
                    display_name=detail.display_name or detail.filename,
                    description=detail.description,
                    score=score,
                    summary=summary,
                )
            )

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[: self.max_profiles]

    def _score(self, text: str, query_terms: Iterable[str]) -> int:
        normalized = text.lower()
        return sum(2 if term in normalized else 0 for term in query_terms)

    def _tokenize(self, query: str) -> List[str]:
        terms = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{2,}", query.lower())
        return [term for term in terms if len(term.strip()) >= 2]

    def _summarize_config(self, data: Dict[str, Any]) -> str:
        highlight_config = data.get("highlight_config") if isinstance(data.get("highlight_config"), dict) else data
        prompt = str(highlight_config.get("extraction_prompt", ""))[:500]

        colors = []
        raw_colors = highlight_config.get("category_colors", [])
        if isinstance(raw_colors, list):
            for item in raw_colors:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                description = str(item.get("description", "")).strip()
                if name or description:
                    colors.append(f"{name}:{description}".strip(":"))

        classes = []
        raw_examples = highlight_config.get("examples", [])
        if isinstance(raw_examples, list):
            for example in raw_examples:
                if not isinstance(example, dict):
                    continue
                for extraction in example.get("extractions", []) or []:
                    if isinstance(extraction, dict) and extraction.get("class"):
                        classes.append(str(extraction["class"]))

        parts = []
        if prompt:
            parts.append(f"prompt={prompt}")
        if colors:
            parts.append(f"categories={', '.join(colors[:12])}")
        if classes:
            parts.append(f"example_classes={', '.join(sorted(set(classes))[:12])}")
        return " | ".join(parts)

