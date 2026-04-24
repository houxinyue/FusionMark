"""
Workspace 管理模块

提供任务级临时工作区的创建、查询和清理。
工作区用于承载 MinerU 解压、PDF 渲染、LangExtract debug 等必须依赖本地文件路径的操作。
任务完成后，工作区内容上传到 Storage Provider，然后根据配置自动清理。

使用方式:
    from services.storage.workspace import get_workspace_dir, cleanup_workspace
    ws = get_workspace_dir(task_id)
    # ... 使用 ws/mineru, ws/highlight 作为输出目录 ...
    cleanup_workspace(task_id)
"""

import os
import shutil
from pathlib import Path
from typing import Optional


DEFAULT_WORKSPACE_ROOT = "workspaces"


def _get_workspace_root() -> Path:
    """获取工作区根目录"""
    root = os.getenv("WORKSPACE_ROOT", DEFAULT_WORKSPACE_ROOT)
    return Path(root).resolve()


def get_workspace_dir(task_id: str) -> Path:
    """
    获取指定任务的工作区目录

    目录结构: {WORKSPACE_ROOT}/{task_id}/
    其中包含:
        - mineru/    MinerU 输出（zip + extracted）
        - highlight/ Highlight 输出（PDF + debug）

    Args:
        task_id: 任务ID

    Returns:
        工作区目录 Path
    """
    root = _get_workspace_root()
    ws = root / task_id
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def get_mineru_workspace(task_id: str) -> Path:
    """获取 MinerU 工作子目录"""
    ws = get_workspace_dir(task_id) / "mineru"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def get_highlight_workspace(task_id: str) -> Path:
    """获取 Highlight 工作子目录"""
    ws = get_workspace_dir(task_id) / "highlight"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def cleanup_workspace(task_id: str) -> bool:
    """
    清理指定任务的工作区目录

    Args:
        task_id: 任务ID

    Returns:
        是否成功删除
    """
    root = _get_workspace_root()
    ws = root / task_id
    if ws.exists():
        try:
            shutil.rmtree(str(ws))
            return True
        except Exception as e:
            print(f"[!] 清理工作区失败 {task_id}: {e}")
            return False
    return True


def should_cleanup_workspace() -> bool:
    """根据环境变量判断任务完成后是否自动清理工作区"""
    return os.getenv("CLEAN_WORKSPACE_AFTER_UPLOAD", "true").lower() in ("true", "1", "yes")
