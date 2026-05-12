"""LLM-backed Profile YAML draft generation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from openai import OpenAI

from .schemas import DraftGenerationRequest, DraftGenerationResult


class DraftGenerationError(RuntimeError):
    """Base error for draft generation failures."""


class ModelConfigurationError(DraftGenerationError):
    """Raised when model credentials are unavailable."""


@dataclass
class ProfileDraftGeneratorConfig:
    model_id: str = "deepseek-chat"
    api_key_env: str = "DS_API_KEY"
    base_url_env: str = "DS_API_BASE_URL"


class ProfileDraftGenerator:
    """Generate raw YAML drafts through an OpenAI-compatible chat API."""

    def __init__(self, config: ProfileDraftGeneratorConfig | None = None) -> None:
        self.config = config or ProfileDraftGeneratorConfig()

    def generate(self, request: DraftGenerationRequest) -> DraftGenerationResult:
        api_key = os.getenv(self.config.api_key_env)
        base_url = os.getenv(self.config.base_url_env)
        if not api_key:
            raise ModelConfigurationError(f"Missing model API key environment variable: {self.config.api_key_env}")

        client = OpenAI(api_key=api_key, base_url=base_url or None)
        response = client.chat.completions.create(
            model=self.config.model_id,
            messages=self._build_messages(request),
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        draft_yaml = self._extract_yaml(content)
        assistant_message = self._summarize_response(content, draft_yaml)
        return DraftGenerationResult(assistant_message=assistant_message, draft_yaml=draft_yaml)

    def _build_messages(self, request: DraftGenerationRequest) -> List[dict]:
        config_guidance = _load_fusion_mark_config_guidance()
        system_prompt = (
            "You are Fusion-Mark Config Copilot. Generate only Fusion-Mark Profile YAML drafts. "
            "The YAML must be compatible with FullPipelineConfig. highlight_config MUST be a mapping/object, "
            "never a list. Do not use regex-rule-list fields such as pattern, group, or label because this "
            "project uses LangExtract prompts, examples, and category_colors instead. Do not include API keys "
            "or secrets. Do not save, activate, delete, or claim to modify real profiles. Return a short "
            "explanation and a YAML code block.\n\n"
            "Project-specific configuration guidance follows. Treat it as authoritative:\n"
            f"{config_guidance}"
        )
        context_lines = []
        for profile in request.referenced_profiles:
            context_lines.append(
                f"- {profile.profile_id} ({profile.display_name}): {profile.description or ''}\n  {profile.summary}"
            )
        context = "\n".join(context_lines) or "No existing profile context."

        user_prompt = (
            f"User request:\n{request.user_message}\n\n"
            f"Current draft YAML, if any:\n{request.current_draft_yaml or '(none)'}\n\n"
            f"Relevant existing profiles:\n{context}\n\n"
            "Use this exact structure pattern and adapt the category names/descriptions/examples:\n"
            "description: \"...\"\n"
            "highlight_config:\n"
            "  extraction_prompt: |\n"
            "    Extract these classes from the document: class_a, class_b.\n"
            "    Use exact source text.\n"
            "  examples:\n"
            "    - text: \"sample text\"\n"
            "      extractions:\n"
            "        - class: class_a\n"
            "          text: \"sample value\"\n"
            "  model_config:\n"
            "    model_id: \"deepseek-chat\"\n"
            "    provider: \"OpenAILanguageModel\"\n"
            "    api_key_env: \"DS_API_KEY\"\n"
            "    base_url_env: \"DS_API_BASE_URL\"\n"
            "    provider_kwargs: {}\n"
            "  category_colors:\n"
            "    - name: class_a\n"
            "      color: \"#2ecc71\"\n"
            "      description: \"...\"\n"
            "  renderer: \"dom_tracking\"\n"
            "final_output_dir: \"highlight_output\"\n\n"
            "Return a concise assistant explanation and then a complete YAML draft in one fenced yaml block."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _extract_yaml(self, content: str) -> str:
        match = re.search(r"```(?:yaml|yml)?\s*(.*?)```", content, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.strip()

    def _summarize_response(self, content: str, draft_yaml: str) -> str:
        if not draft_yaml:
            return content.strip()
        explanation = content.replace(draft_yaml, "").replace("```yaml", "").replace("```", "").strip()
        return explanation or "已生成 Profile YAML 草稿，请检查校验结果后再应用到编辑器。"


@lru_cache(maxsize=1)
def _load_fusion_mark_config_guidance() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    skill_path = repo_root / ".agents" / "skills" / "fusion-mark-config" / "SKILL.md"
    template_path = repo_root / ".agents" / "skills" / "fusion-mark-config" / "assets" / "config-template.yaml"

    parts: List[str] = []
    if skill_path.exists():
        parts.append(skill_path.read_text(encoding="utf-8"))
    else:
        parts.append(
            "Valid profiles use FullPipelineConfig with highlight_config as a mapping containing "
            "extraction_prompt, examples, model_config, category_colors, renderer, and output paths."
        )

    if template_path.exists():
        parts.append("\nAuthoritative profile template:\n```yaml\n")
        parts.append(template_path.read_text(encoding="utf-8"))
        parts.append("\n```")

    return "\n".join(parts)
