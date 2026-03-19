"""
第三方 API 客户端模块

提供对外部服务的客户端封装:
    - mineru: MinerU API 客户端
"""

from .mineru import MinerUClient, MinerUConfig, ParseResult

__all__ = ["MinerUClient", "MinerUConfig", "ParseResult"]
