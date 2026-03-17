"""
Celery Chain Pipeline - 全异步工作流架构

将 MinerU → LangExtract → 高亮渲染 全流程改造为 Celery Chain

使用方式:
    1. 启动 Worker:
       celery -A celery_chain_pipeline.celery_config worker -l info -Q pdf_processing
    
    2. 启动 API 服务:
       uvicorn celery_chain_pipeline.api_server:app --reload --port 8000

目录结构:
    celery_chain_pipeline/
    ├── __init__.py
    ├── celery_config.py      # Celery 应用配置
    ├── celery_tasks.py       # 三个步骤任务定义
    ├── progress_manager.py   # 统一进度管理器
    ├── websocket_handler.py  # WebSocket 进度推送
    └── api_server.py         # FastAPI 服务
"""

__version__ = "2.0.0"
__all__ = [
    "celery_app",
    "ProgressManager",
    "WebSocketProgressHandler",
    "step1_mineru_parse",
    "step2_langextract",
    "step3_highlight_render",
]

# 延迟导入，避免循环依赖
def _get_celery_app():
    from .celery_config import celery_app
    return celery_app


def _get_progress_manager():
    from .progress_manager import ProgressManager
    return ProgressManager


def _get_websocket_handler():
    from .websocket_handler import WebSocketProgressHandler
    return WebSocketProgressHandler
