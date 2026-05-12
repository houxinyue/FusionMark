"""YAML validation for Profile Config Copilot drafts."""

from __future__ import annotations

from typing import Any, Dict

import yaml

from services.core.full_pipeline import FullPipelineConfig

from .schemas import CopilotValidationResult


class ProfileDraftValidator:
    """Validate raw YAML without rewriting user-visible content."""

    def validate(self, content: str) -> CopilotValidationResult:
        if not content or not content.strip():
            return CopilotValidationResult(valid=False, errors=["YAML 内容不能为空。"])

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            return CopilotValidationResult(valid=False, errors=[f"YAML 格式错误: {exc}"])

        if not isinstance(data, dict):
            return CopilotValidationResult(valid=False, errors=["YAML 根节点必须是对象。"])

        highlight_config = data.get("highlight_config")
        if isinstance(highlight_config, list):
            return CopilotValidationResult(
                valid=False,
                errors=[
                    "highlight_config 必须是对象，不能是列表。请使用 highlight_config.extraction_prompt、"
                    "highlight_config.category_colors 和 highlight_config.examples 描述抽取类别；"
                    "当前系统不支持 pattern/group/label 规则数组格式。"
                ],
            )

        try:
            config = FullPipelineConfig.from_dict(data)
        except Exception as exc:
            return CopilotValidationResult(valid=False, errors=[f"Profile 配置校验失败: {exc}"])

        return CopilotValidationResult(valid=True, errors=[], config=config.to_dict())

    @staticmethod
    def parse_mapping(content: str) -> Dict[str, Any]:
        data = yaml.safe_load(content) or {}
        if not isinstance(data, dict):
            return {}
        return data
