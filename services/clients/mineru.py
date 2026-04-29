"""
MinerU Client - 文档解析工具常量与数据结构

保留 MinerU 配置、解析结果数据类以及通用常量/工具方法，
供 MinerU Provider 层使用。旧的手写 v4 API 客户端已移除，
统一使用 mineru_provider 中的 OpenSdkMinerUProvider。

环境变量:
    MINERU_API_KEY: MinerU API 密钥（必需）

作者: AI Assistant
日期: 2026-02-04
"""

import os
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量 (从 services/ 目录)
_ENV_PATH = Path(__file__).parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()


@dataclass
class MinerUConfig:
    """MinerU 配置类"""
    api_key: str
    base_url: str = "https://mineru.net/api/v4/extract"
    output_dir: str = "./mineru_output"
    poll_interval: int = 3          # 轮询间隔（秒）
    max_poll_retries: int = 60      # 最大轮询次数，<=0 表示无限轮询
    download_timeout: int = 300     # 下载超时（秒）
    provider_mode: str = "open_sdk"
    sdk_base_url: str = "https://mineru.net/api/v4"
    sdk_token: str = ""
    sdk_token_env: str = "MINERU_API_KEY"
    sdk_extra_formats: Optional[List[str]] = None


@dataclass
class ParseResult:
    """解析结果数据类"""
    task_id: str
    state: str                      # done, failed, pending, running
    zip_url: str
    zip_path: str                   # 本地ZIP文件路径
    extract_dir: str                # 解压目录
    content: Optional[str] = None   # Markdown 内容
    error_msg: Optional[str] = None # 错误信息


class MinerUClient:
    """
    MinerU 客户端常量与工具方法容器。

    旧的手写 v4 API 调用逻辑（create_task / wait_for_completion /
    download_result / process_document 等）已移除，请使用
    mineru_provider 模块中的 MinerUProviderFactory 获取统一解析器。
    """

    # 模型版本常量
    MODEL_PIPELINE = "pipeline"      # 快速解析，默认
    MODEL_VLM = "vlm"                # 视觉语言模型，高精度
    MODEL_HTML = "MinerU-HTML"       # HTML 专用

    # 任务状态常量
    STATE_PENDING = "pending"
    STATE_RUNNING = "running"
    STATE_CONVERTING = "converting"
    STATE_DONE = "done"
    STATE_FAILED = "failed"

    @staticmethod
    def read_markdown(extract_dir: str) -> Optional[str]:
        """
        读取解压目录中的 Markdown 内容

        MinerU 默认生成 full.md 作为主内容文件

        Args:
            extract_dir: 解压目录路径

        Returns:
            Markdown 文本内容，失败返回 None
        """
        # 可能的 Markdown 文件名
        candidates = ['full.md', 'result.md', 'output.md', 'content.md']

        # 查找文件
        md_path = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() in candidates:
                    md_path = os.path.join(root, file)
                    break
            if md_path:
                break

        if not md_path:
            print(f"[警告] 未找到 Markdown 文件")
            return None

        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"[读取] ✓ 已读取 {len(content)} 字符")
            return content

        except Exception as e:
            print(f"[错误] 读取失败: {e}")
            return None
