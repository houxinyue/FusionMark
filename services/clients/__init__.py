"""
第三方 API 客户端模块

提供对外部服务的客户端封装:
    - mineru: MinerU API 客户端（统一通过 Provider Factory 获取）
"""

from .mineru import MinerUConfig, ParseResult
from .mineru_provider import MinerUProviderFactory

__all__ = ["MinerUConfig", "ParseResult", "MinerUProviderFactory"]
