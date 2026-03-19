"""
核心业务逻辑模块

提供主要业务服务:
    - highlight: MD 高亮服务
    - full_pipeline: 完整流程服务
"""

from .highlight import (
    MDHighlightService,
    MDHighlightConfig,
    LangExtractExample,
    CategoryColor,
    ModelProviderConfig,
    ServiceResult
)
from .full_pipeline import (
    FullPipelineService,
    FullPipelineConfig,
    PipelineResult
)

__all__ = [
    # Highlight
    "MDHighlightService",
    "MDHighlightConfig",
    "LangExtractExample",
    "CategoryColor",
    "ModelProviderConfig",
    "ServiceResult",
    # Full Pipeline
    "FullPipelineService",
    "FullPipelineConfig",
    "PipelineResult",
]
