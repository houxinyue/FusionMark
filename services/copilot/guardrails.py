"""Deterministic guardrails for Profile Config Copilot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""


class CopilotGuardrails:
    """Keep Copilot focused on Fusion-Mark Profile configuration."""

    _blocked_keywords = (
        "删除profile",
        "删除 profile",
        "delete profile",
        "remove profile",
        "rm ",
        "del ",
        "powershell",
        "cmd.exe",
        "运行命令",
        "执行命令",
        "shell",
        "读取文件",
        "写文件",
        "file system",
        "天气",
        "新闻",
        "股票",
        "改代码",
        "修改代码",
        "application code",
    )
    _profile_keywords = (
        "profile",
        "yaml",
        "配置",
        "高亮",
        "highlight",
        "langextract",
        "mineru",
        "ocr",
        "类别",
        "颜色",
        "提示词",
        "few-shot",
        "few shot",
        "抽取",
        "实体",
    )

    def check(self, message: str) -> GuardrailResult:
        normalized = message.strip().lower()
        if not normalized:
            return GuardrailResult(False, "请输入要生成或修改的 Profile 配置需求。")

        if any(keyword in normalized for keyword in self._blocked_keywords):
            return GuardrailResult(
                False,
                "我只能帮助创建或修改 Fusion-Mark Profile YAML 草稿，不能执行系统命令、访问任意文件、删除配置或处理无关请求。",
            )

        if not any(keyword in normalized for keyword in self._profile_keywords):
            return GuardrailResult(
                False,
                "这个请求看起来不属于 Fusion-Mark Profile 配置范围。请描述要高亮的文档类型、抽取类别、颜色或 MinerU/LangExtract 配置需求。",
            )

        return GuardrailResult(True)

