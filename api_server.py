"""
FastAPI Web 服务 - PDF 智能解析与高亮 API

提供 RESTful API 接口，支持:
- 提交 PDF 处理任务
- 查询任务状态
- 下载结果文件
- 实时进度推送 (WebSocket)

启动方式:
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

依赖安装:
    pip install fastapi uvicorn websockets celery redis
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from full_pipeline_service import FullPipelineService, FullPipelineConfig, PipelineResult

# ============ 数据模型 ============

class SubmitTaskRequest(BaseModel):
    """提交任务请求"""
    pdf_url: HttpUrl = Field(..., description="PDF 文件 URL")
    output_filename: Optional[str] = Field(None, description="输出文件名")
    custom_title: Optional[str] = Field(None, description="文档标题")
    custom_prompt: Optional[str] = Field(None, description="自定义提取提示词")
    # MinerU 参数
    model: str = Field("vlm", description="MinerU 模型: pipeline/vlm/MinerU-HTML")
    enable_ocr: bool = Field(True, description="启用 OCR")
    enable_formula: bool = Field(True, description="启用公式识别")
    enable_table: bool = Field(True, description="启用表格识别")
    language: str = Field("ch", description="文档语言")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str  # pending, processing, completed, failed
    message: str
    created_at: str
    updated_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: Dict[str, Any]
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ConfigRequest(BaseModel):
    """配置请求"""
    config: Dict[str, Any] = Field(..., description="完整配置 JSON")


# ============ 任务管理器 ============

class TaskManager:
    """任务管理器 - 管理任务状态和进度"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.progress_callbacks: Dict[str, List[callable]] = {}
    
    def create_task(self, task_id: str, pdf_url: str) -> Dict[str, Any]:
        """创建新任务"""
        task = {
            "task_id": task_id,
            "pdf_url": pdf_url,
            "status": "pending",
            "message": "任务已创建，等待处理",
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
            "progress": {
                "mineru_state": "pending",
                "mineru_progress": 0,
                "extraction_count": 0,
                "highlight_count": 0
            },
            "result": None
        }
        self.tasks[task_id] = task
        self.progress_callbacks[task_id] = []
        return task
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
            
            # 触发进度回调
            for callback in self.progress_callbacks.get(task_id, []):
                try:
                    callback(self.tasks[task_id])
                except Exception:
                    pass
    
    def update_progress(self, task_id: str, **progress):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id]["progress"].update(progress)
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
            
            # 触发进度回调
            for callback in self.progress_callbacks.get(task_id, []):
                try:
                    callback(self.tasks[task_id])
                except Exception:
                    pass
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def register_progress_callback(self, task_id: str, callback: callable):
        """注册进度回调"""
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)
    
    def unregister_progress_callback(self, task_id: str, callback: callable):
        """取消注册进度回调"""
        if task_id in self.progress_callbacks:
            if callback in self.progress_callbacks[task_id]:
                self.progress_callbacks[task_id].remove(callback)


# 全局任务管理器
task_manager = TaskManager()

# 全局服务实例
pipeline_service: Optional[FullPipelineService] = None


def get_service() -> FullPipelineService:
    """获取或创建服务实例"""
    global pipeline_service
    if pipeline_service is None:
        config = FullPipelineConfig()
        pipeline_service = FullPipelineService(config)
    return pipeline_service


# ============ FastAPI 应用 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 启动 PDF 智能解析服务...")
    get_service()
    yield
    # 关闭时清理
    print("🛑 关闭服务...")


app = FastAPI(
    title="PDF 智能解析与高亮 API",
    description="整合 MinerU + LangExtract + 高亮渲染的 PDF 处理服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ API 路由 ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "PDF 智能解析与高亮 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "submit_task": "POST /api/v1/tasks",
            "get_task": "GET /api/v1/tasks/{task_id}",
            "list_tasks": "GET /api/v1/tasks",
            "download": "GET /api/v1/tasks/{task_id}/download",
            "websocket": "WS /ws/{task_id}"
        }
    }


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def submit_task(
    request: SubmitTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    提交 PDF 处理任务
    
    任务将异步执行，返回 task_id 用于查询状态
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task_manager.create_task(task_id, str(request.pdf_url))
    
    # 后台执行处理
    background_tasks.add_task(
        process_pdf_task,
        task_id=task_id,
        request=request
    )
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="任务已提交，正在处理中",
        created_at=datetime.now().isoformat()
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询任务状态"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        message=task.get("message"),
        result=task.get("result")
    )


@app.get("/api/v1/tasks")
async def list_tasks(limit: int = 10, offset: int = 0):
    """列出最近任务"""
    tasks = list(task_manager.tasks.values())
    tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total": len(tasks),
        "limit": limit,
        "offset": offset,
        "tasks": tasks[offset:offset + limit]
    }


@app.get("/api/v1/tasks/{task_id}/download")
async def download_result(task_id: str):
    """下载处理结果 PDF"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    result = task.get("result", {})
    output_path = result.get("output_path")
    
    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    return FileResponse(
        path=output_path,
        filename=Path(output_path).name,
        media_type="application/pdf"
    )


@app.post("/api/v1/config")
async def update_config(request: ConfigRequest):
    """更新服务配置（动态重载）"""
    global pipeline_service
    
    try:
        config = FullPipelineConfig.from_dict(request.config)
        pipeline_service = FullPipelineService(config)
        return {"success": True, "message": "配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置更新失败: {str(e)}")


@app.get("/api/v1/config/default")
async def get_default_config():
    """获取默认配置"""
    config = FullPipelineConfig()
    return config.to_dict()


# ============ WebSocket 实时进度 ============

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 实时进度推送
    
    连接后，服务端会实时推送任务进度更新
    """
    await websocket.accept()
    
    task = task_manager.get_task(task_id)
    if not task:
        await websocket.send_json({"error": "任务不存在"})
        await websocket.close()
        return
    
    # 定义进度回调
    async def progress_callback(task_data: Dict[str, Any]):
        await websocket.send_json({
            "type": "progress",
            "data": task_data
        })
    
    # 注册回调
    callback_id = id(progress_callback)
    task_manager.register_progress_callback(task_id, lambda t: asyncio.create_task(progress_callback(t)))
    
    try:
        # 发送当前状态
        await websocket.send_json({
            "type": "connected",
            "data": task
        })
        
        # 保持连接，接收客户端心跳
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        print(f"WebSocket 断开: {task_id}")
    finally:
        task_manager.unregister_progress_callback(task_id, progress_callback)


# ============ 后台任务处理 ============

def process_pdf_task(task_id: str, request: SubmitTaskRequest):
    """后台处理 PDF 任务"""
    
    # 更新任务状态
    task_manager.update_task(task_id, status="processing", message="MinerU 解析中...")
    
    try:
        # 创建带进度回调的服务配置
        config = FullPipelineConfig()
        config.mineru_model = request.model
        config.mineru_enable_ocr = request.enable_ocr
        config.mineru_enable_formula = request.enable_formula
        config.mineru_enable_table = request.enable_table
        config.mineru_language = request.language
        
        service = FullPipelineService(config)
        
        # 定义 MinerU 进度回调
        def mineru_progress_callback(attempt: int, state: str, data: Dict):
            progress = data.get("extract_progress", {})
            task_manager.update_progress(
                task_id,
                mineru_state=state,
                mineru_progress=progress.get("extracted_pages", 0),
                mineru_total=progress.get("total_pages", 0),
                mineru_attempt=attempt
            )
        
        # 处理 PDF
        result = service.process_pdf(
            url=str(request.pdf_url),
            output_filename=request.output_filename,
            custom_prompt=request.custom_prompt,
            custom_title=request.custom_title
        )
        
        if result.success:
            # 构建结果
            result_data = {
                "task_id": result.task_id,
                "output_path": str(result.output_path) if result.output_path else None,
                "md_length": len(result.md_content) if result.md_content else 0,
                "extraction_count": result.highlight_result.extraction_count if result.highlight_result else 0,
                "highlight_count": result.highlight_result.highlight_count if result.highlight_result else 0,
                "category_counts": result.highlight_result.details.get("category_counts", {}) if result.highlight_result else {}
            }
            
            task_manager.update_task(
                task_id,
                status="completed",
                message="处理完成",
                result=result_data
            )
            task_manager.update_progress(
                task_id,
                extraction_count=result_data["extraction_count"],
                highlight_count=result_data["highlight_count"]
            )
        else:
            task_manager.update_task(
                task_id,
                status="failed",
                message=result.message
            )
            
    except Exception as e:
        task_manager.update_task(
            task_id,
            status="failed",
            message=f"处理异常: {str(e)}"
        )


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tasks": {
            "total": len(task_manager.tasks),
            "pending": sum(1 for t in task_manager.tasks.values() if t["status"] == "pending"),
            "processing": sum(1 for t in task_manager.tasks.values() if t["status"] == "processing"),
            "completed": sum(1 for t in task_manager.tasks.values() if t["status"] == "completed"),
            "failed": sum(1 for t in task_manager.tasks.values() if t["status"] == "failed"),
        }
    }


# ============ 主入口 ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
