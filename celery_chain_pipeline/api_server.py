"""
FastAPI Web 服务 - Celery Chain Pipeline API

提供 RESTful API 接口，支持:
- 提交 PDF 处理任务 (Celery Chain)
- 查询任务状态
- 下载结果文件
- 实时进度推送 (WebSocket)

启动方式:
    uvicorn celery_chain_pipeline.api_server:app --reload --host 0.0.0.0 --port 8000

依赖:
    - Redis (任务队列和进度存储)
    - Celery Worker (任务执行)
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# 导入 Celery Chain Pipeline 模块
from celery_chain_pipeline.celery_config import get_celery_app
from celery_chain_pipeline.progress_manager import get_progress_manager
from celery_chain_pipeline.websocket_handler import handle_websocket
from celery_chain_pipeline.celery_tasks import submit_pipeline


# ============ 生命周期管理 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("[API] Celery Chain Pipeline API 启动中...")
    
    # 验证 Redis 连接
    try:
        progress_manager = get_progress_manager()
        progress_manager.redis.ping()
        print("[API] Redis 连接成功")
    except Exception as e:
        print(f"[API] Redis 连接失败: {e}")
        raise
    
    yield
    
    # 关闭时
    print("[API] Celery Chain Pipeline API 关闭")


# ============ FastAPI 应用 ============

app = FastAPI(
    title="FusionMark Celery Chain API",
    description="全异步 PDF 处理 Pipeline API - Celery Chain 架构",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 数据模型 ============

class SubmitTaskRequest(BaseModel):
    """提交任务请求"""
    document_url: str = Field(..., description="文档URL，支持 pdf/doc/docx/ppt/pptx/png/jpg/jpeg/html")
    output_filename: Optional[str] = Field(None, description="输出文件名")
    custom_title: Optional[str] = Field(None, description="文档标题")
    custom_prompt: Optional[str] = Field(None, description="自定义提取提示词")
    # MinerU 参数
    model: str = Field("vlm", description="MinerU 模型: pipeline/vlm/MinerU-HTML")
    enable_ocr: bool = Field(True, description="启用 OCR")
    enable_formula: bool = Field(True, description="启用公式识别")
    enable_table: bool = Field(True, description="启用表格识别")
    language: str = Field("ch", description="文档语言")
    
    @field_validator('document_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证URL格式"""
        if not v or not v.strip():
            raise ValueError('URL不能为空')
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL必须以 http:// 或 https:// 开头')
        return v


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str  # pending, processing, completed, failed
    message: str
    created_at: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    current_stage: Optional[str] = None
    overall_progress: int
    stages: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    redis: str
    timestamp: str


# ============ API 路由 ============

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径 - API 信息"""
    return {
        "name": "FusionMark Celery Chain API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    try:
        progress_manager = get_progress_manager()
        progress_manager.redis.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="ok" if redis_status == "connected" else "degraded",
        version="2.0.0",
        redis=redis_status,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def submit_task(request: SubmitTaskRequest):
    """
    提交 PDF 处理任务
    
    任务将异步执行以下流程:
    1. MinerU 文档解析
    2. LangExtract 实体提取
    3. 高亮渲染生成 PDF
    
    通过 WebSocket /ws/{task_id} 获取实时进度
    """
    # 生成任务 ID
    task_id = str(uuid.uuid4())
    
    # 构建配置
    config = {
        "output_filename": request.output_filename,
        "custom_title": request.custom_title,
        "custom_prompt": request.custom_prompt,
        "model": request.model,
        "enable_ocr": request.enable_ocr,
        "enable_formula": request.enable_formula,
        "enable_table": request.enable_table,
        "language": request.language,
    }
    
    try:
        # 提交 Celery Chain Pipeline
        result = submit_pipeline(
            pipeline_task_id=task_id,
            document_url=request.document_url,
            config=config
        )
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="任务已提交，正在排队处理中",
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"提交任务失败: {str(e)}"
        )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询任务状态和进度"""
    progress_manager = get_progress_manager()
    
    progress = progress_manager.get_task_progress(task_id)
    
    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"任务 {task_id} 不存在或已过期"
        )
    
    return TaskStatusResponse(
        task_id=progress['task_id'],
        status=progress['status'],
        current_stage=progress['current_stage'],
        overall_progress=progress['overall_progress'],
        stages=progress['stages'],
        created_at=progress['created_at'],
        updated_at=progress['updated_at']
    )


@app.get("/api/v1/tasks/{task_id}/download")
async def download_result(task_id: str):
    """下载处理结果文件"""
    progress_manager = get_progress_manager()
    
    # 检查任务状态
    progress = progress_manager.get_task_progress(task_id)
    
    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"任务 {task_id} 不存在"
        )
    
    if progress['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {progress['status']}"
        )
    
    # 构建输出文件路径
    output_path = Path("highlight_output") / f"{task_id}.pdf"
    
    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="结果文件不存在"
        )
    
    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="application/pdf"
    )


@app.get("/api/v1/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="按状态过滤: pending/processing/completed/failed"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取任务列表 (简化版)
    
    实际项目中可以查询数据库，这里仅作示例
    """
    # 这里可以实现从数据库查询任务列表
    # 目前返回示例数据
    return {
        "tasks": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


# ============ WebSocket 路由 ============

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 实时进度推送
    
    连接后自动接收任务进度更新:
    - progress: 进度更新
    - completed: 任务完成
    - failed: 任务失败
    
    客户端可以发送:
    - ping: 心跳检测
    - get_progress: 主动查询当前进度
    """
    await handle_websocket(websocket, task_id)


# ============ 错误处理 ============

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "celery_chain_pipeline.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
