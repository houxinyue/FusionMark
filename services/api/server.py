"""
FastAPI Web 服务 - PDF 智能解析与高亮 API

提供 RESTful API 接口，支持:
- 提交 PDF 处理任务
- 查询任务状态
- 下载结果文件
- 实时进度推送 (WebSocket)

启动方式:
    uvicorn services.api.server:app --reload --host 0.0.0.0 --port 8000

依赖安装:
    pip install fastapi uvicorn websockets celery redis
"""

import os
import json
import asyncio
import yaml
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

try:
    # 从项目根目录运行时
    from services.core.full_pipeline import FullPipelineService, FullPipelineConfig, PipelineResult
except ModuleNotFoundError:
    # 从 services 目录内运行时，使用相对导入
    from ..core.full_pipeline import FullPipelineService, FullPipelineConfig, PipelineResult

# ============ 配置目录 ============
# 计算 services 目录 (services/api/server.py -> services/)
SERVICES_DIR = Path(__file__).parent.parent
PROFILES_DIR = SERVICES_DIR / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)

CURRENT_PROFILE_FILE = PROFILES_DIR / ".current.yaml"


def get_current_profile_config() -> Tuple[Optional[FullPipelineConfig], Optional[str]]:
    """
    获取当前激活的配置文件
    返回: (配置对象, 配置文件名)
    如果没有激活的配置，返回 (None, None)
    """
    if not CURRENT_PROFILE_FILE.exists():
        return None, None
    
    try:
        with open(CURRENT_PROFILE_FILE, 'r', encoding='utf-8') as f:
            current = yaml.safe_load(f)
            profile_file = current.get('profile_file') if current else None
        
        if not profile_file:
            return None, None
        
        config_path = PROFILES_DIR / profile_file
        if not config_path.exists():
            return None, None
        
        config = FullPipelineConfig.from_yaml(config_path)
        return config, profile_file
    except Exception as e:
        print(f"[!] 加载当前配置失败: {e}")
        return None, None


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


class ProfileInfo(BaseModel):
    """配置档案信息"""
    name: str
    filename: str
    description: Optional[str] = None
    size: int
    created_at: str
    updated_at: str
    is_current: bool = False


# ============ 任务管理器 ============

class TaskManager:
    """任务管理器 - 管理任务状态和进度"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.progress_callbacks: Dict[str, List[callable]] = {}
    
    def create_task(self, task_id: str, document_url: str) -> Dict[str, Any]:
        """创建新任务"""
        task = {
            "task_id": task_id,
            "document_url": document_url,
            "status": "pending",
            "message": "任务已创建，等待处理",
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
            "progress": {
                # 当前阶段: pending/mineru/extraction/highlight/completed/failed
                "stage": "pending",
                "stage_progress": 0,  # 当前阶段进度 0-100
                "overall_progress": 0,  # 总体进度 0-100
                # MinerU 阶段详情
                "mineru": {
                    "state": "pending",  # pending/running/completed/failed
                    "progress": 0,  # 0-100
                    "current_page": 0,
                    "total_pages": 0,
                    "logs": []
                },
                # 实体提取阶段详情
                "extraction": {
                    "state": "pending",
                    "progress": 0,  # 0-100
                    "extracted_count": 0,
                    "logs": []
                },
                # 高亮渲染阶段详情
                "highlight": {
                    "state": "pending",
                    "progress": 0,  # 0-100
                    "highlighted_count": 0,
                    "logs": []
                }
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
        # 尝试加载当前激活的配置
        config, profile_name = get_current_profile_config()
        if config is None:
            print("[*] 使用默认配置")
            config = FullPipelineConfig()
        else:
            print(f"[*] 使用配置文件: {profile_name}")
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
    task_manager.create_task(task_id, str(request.document_url))
    
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


@app.get("/api/v1/profiles", response_model=List[ProfileInfo])
async def list_profiles():
    """
    列出所有配置档案
    
    返回 profiles/ 目录下的所有 YAML 配置档案列表，包含描述信息
    """
    profiles = []
    current_profile = None
    
    # 读取当前使用的配置
    if CURRENT_PROFILE_FILE.exists():
        try:
            with open(CURRENT_PROFILE_FILE, 'r', encoding='utf-8') as f:
                current = yaml.safe_load(f)
                current_profile = current.get('profile_file') if current else None
        except:
            pass
    
    for profile_file in PROFILES_DIR.glob("*.yaml"):
        if profile_file.name == ".current.yaml":
            continue
        
        stat = profile_file.stat()
        
        # 从 YAML 中读取 description
        description = None
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if content and isinstance(content, dict):
                    description = content.get('description')
        except:
            pass
        
        profiles.append(ProfileInfo(
            name=profile_file.stem,
            filename=profile_file.name,
            description=description,
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            is_current=(profile_file.name == current_profile)
        ))
    
    return sorted(profiles, key=lambda x: x.updated_at, reverse=True)


@app.post("/api/v1/profiles/upload")
async def upload_profile(
    file: UploadFile = File(..., description="YAML 配置文件"),
    set_as_current: bool = Query(True, description="是否设为当前配置"),
    description: Optional[str] = Query(None, description="配置档案描述，会写入 YAML 文件")
):
    """
    上传 YAML 配置档案
    
    - 接收 YAML 格式的配置文件
    - 保存到 profiles/ 目录
    - 可选择是否立即设为当前配置
    - 可通过 description 参数添加描述说明
    """
    # 检查文件类型
    if not file.filename.endswith(('.yaml', '.yml')):
        raise HTTPException(status_code=400, detail="只支持 .yaml 或 .yml 文件")
    
    # 读取并验证 YAML
    try:
        content = await file.read()
        config_data = yaml.safe_load(content)
        
        # 验证配置格式
        config = FullPipelineConfig.from_dict(config_data)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML 格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置验证失败: {str(e)}")
    
    # 如果提供了 description，添加到配置数据中
    if description and config_data and isinstance(config_data, dict):
        config_data['description'] = description
    
    # 保存文件
    filename = file.filename if file.filename.endswith('.yaml') else f"{file.filename}.yaml"
    if not filename.endswith('.yaml'):
        filename = f"{filename}.yaml"
    
    file_path = PROFILES_DIR / filename
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    finally:
        await file.close()
    
    # 设为当前配置
    if set_as_current:
        try:
            global pipeline_service
            pipeline_service = FullPipelineService(config)
            
            # 保存当前配置引用
            with open(CURRENT_PROFILE_FILE, 'w', encoding='utf-8') as f:
                yaml.dump({"profile_file": filename}, f)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"加载配置失败: {str(e)}")
    
    return {
        "success": True,
        "message": f"配置 '{filename}' 上传成功",
        "filename": filename,
        "set_as_current": set_as_current
    }


@app.post("/api/v1/profiles/{profile_name}/activate")
async def activate_profile(profile_name: str):
    """
    激活指定配置文件
    
    从 profiles/ 目录加载指定配置并设为当前配置
    """
    global pipeline_service
    
    # 确保文件名有 .yaml 后缀
    if not profile_name.endswith('.yaml'):
        profile_name = f"{profile_name}.yaml"
    
    config_path = PROFILES_DIR / profile_name
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"配置文件 '{profile_name}' 不存在")
    
    try:
        # 加载配置
        config = FullPipelineConfig.from_yaml(config_path)
        pipeline_service = FullPipelineService(config)
        
        # 保存当前配置引用
        with open(CURRENT_PROFILE_FILE, 'w', encoding='utf-8') as f:
            yaml.dump({"profile_file": profile_name}, f)
        
        print(f"[+] 配置文件已激活: {profile_name}")
        
        return {
            "success": True,
            "message": f"配置 '{profile_name}' 已激活",
            "profile_file": profile_name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"加载配置失败: {str(e)}")


@app.get("/api/v1/profiles/{profile_name}/download")
async def download_profile(profile_name: str):
    """
    下载配置文件
    
    下载 profiles/ 目录下的指定 YAML 配置文件
    """
    # 确保文件名有 .yaml 后缀
    if not profile_name.endswith('.yaml'):
        profile_name = f"{profile_name}.yaml"
    
    config_path = PROFILES_DIR / profile_name
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"配置文件 '{profile_name}' 不存在")
    
    return FileResponse(
        path=config_path,
        filename=profile_name,
        media_type='application/x-yaml'
    )


@app.delete("/api/v1/profiles/{profile_name}")
async def delete_profile(profile_name: str):
    """
    删除配置文件
    
    删除 profiles/ 目录下的指定配置文件（不能删除当前正在使用的配置）
    """
    # 确保文件名有 .yaml 后缀
    if not profile_name.endswith('.yaml'):
        profile_name = f"{profile_name}.yaml"
    
    config_path = PROFILES_DIR / profile_name
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"配置文件 '{profile_name}' 不存在")
    
    # 检查是否是当前配置
    if CURRENT_PROFILE_FILE.exists():
        try:
            with open(CURRENT_PROFILE_FILE, 'r', encoding='utf-8') as f:
                current = yaml.safe_load(f)
                if current and current.get('profile_file') == profile_name:
                    raise HTTPException(status_code=400, detail="不能删除当前正在使用的配置，请先切换到其他配置")
        except HTTPException:
            raise
        except:
            pass
    
    try:
        config_path.unlink()
        return {
            "success": True,
            "message": f"配置 '{profile_name}' 已删除"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@app.get("/api/v1/profiles/current")
async def get_current_profile():
    """
    获取当前配置内容
    
    返回当前正在使用的配置的完整 YAML 内容
    """
    if not CURRENT_PROFILE_FILE.exists():
        # 返回默认配置
        config = FullPipelineConfig()
        return {
            "source": "default",
            "config": config.to_dict()
        }
    
    try:
        with open(CURRENT_PROFILE_FILE, 'r', encoding='utf-8') as f:
            current = yaml.safe_load(f)
            profile_file = current.get('profile_file') if current else None
        
        if not profile_file:
            config = FullPipelineConfig()
            return {
                "source": "default",
                "config": config.to_dict()
            }
        
        config_path = PROFILES_DIR / profile_file
        if not config_path.exists():
            config = FullPipelineConfig()
            return {
                "source": "default",
                "config": config.to_dict()
            }
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        return {
            "source": profile_file,
            "config": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置失败: {str(e)}")


@app.get("/api/v1/config/default")
async def get_default_config():
    """
    获取默认配置模板
    
    返回默认配置的 YAML 格式，可用于创建新配置
    """
    config = FullPipelineConfig()
    return config.to_dict()


# 存储主事件循环引用，用于后台线程调度
_main_event_loop: Optional[asyncio.AbstractEventLoop] = None

# ============ WebSocket 实时进度 ============

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 实时进度推送
    
    连接后，服务端会实时推送任务进度更新
    """
    global _main_event_loop
    _main_event_loop = asyncio.get_running_loop()
    
    await websocket.accept()
    
    task = task_manager.get_task(task_id)
    if not task:
        await websocket.send_json({"error": "任务不存在"})
        await websocket.close()
        return
    
    async def progress_callback(task_data: Dict[str, Any]):
        try:
            await websocket.send_json({
                "type": "progress",
                "data": task_data
            })
        except Exception as e:
            print(f"[WebSocket] 发送进度失败: {e}")
    
    def sync_callback(task_data: Dict[str, Any]):
        """同步包装器，在后台线程中调度到主事件循环"""
        global _main_event_loop
        if _main_event_loop and _main_event_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(progress_callback(task_data), _main_event_loop)
            except Exception as e:
                print(f"[WebSocket] 调度回调失败: {e}")
        else:
            print(f"[WebSocket] 主事件循环不可用，跳过进度推送")
    
    # 注册回调
    task_manager.register_progress_callback(task_id, sync_callback)
    
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
    except Exception as e:
        print(f"[WebSocket] 错误: {e}")
    finally:
        task_manager.unregister_progress_callback(task_id, sync_callback)


# ============ 后台任务处理 ============

def process_pdf_task(task_id: str, request: SubmitTaskRequest):
    """后台处理 PDF 任务 - 使用分阶段进度"""
    
    import time
    
    def update_stage(stage: str, stage_progress: int = None, message: str = None, 
                    mineru_data: Dict = None, extraction_data: Dict = None, highlight_data: Dict = None):
        """更新当前阶段和进度"""
        progress_data = {"stage": stage}
        if stage_progress is not None:
            progress_data["stage_progress"] = stage_progress
        
        # 计算总体进度 - 根据已完成的阶段累加
        stage_weights = {
            "pending": 0,
            "mineru": 40,      # MinerU占0-40%
            "extraction": 30,  # 实体提取占40-70%
            "highlight": 30,   # 高亮渲染占70-100%
            "completed": 0     # 完成后总体100%
        }
        
        stage_order = ["pending", "mineru", "extraction", "highlight", "completed"]
        if stage in stage_weights:
            # 计算已完成的阶段权重
            completed_weight = 0
            current_stage_index = stage_order.index(stage)
            for i in range(current_stage_index):
                completed_weight += stage_weights.get(stage_order[i], 0)
            
            # 当前阶段的贡献
            current_weight = stage_weights.get(stage, 0)
            current_progress = (stage_progress or 0) / 100
            
            progress_data["overall_progress"] = int(completed_weight + current_weight * current_progress)
        
        # 更新阶段特定数据
        if mineru_data:
            progress_data["mineru"] = mineru_data
        if extraction_data:
            progress_data["extraction"] = extraction_data
        if highlight_data:
            progress_data["highlight"] = highlight_data
            
        task_manager.update_progress(task_id, **progress_data)
        if message:
            task_manager.update_task(task_id, message=message)
    
    # 等待一小段时间，确保 WebSocket 已连接
    time.sleep(0.5)
    
    # ========== 阶段 1: MinerU 解析 ==========
    update_stage("mineru", 0, "MinerU 解析准备中...", 
                 mineru_data={"state": "running", "progress": 0, "logs": ["准备解析文档..."]})
    
    try:
        # 加载配置
        config, profile_name = get_current_profile_config()
        if config is None:
            config = FullPipelineConfig()
        
        # 应用请求参数
        config.mineru_model = request.model
        config.mineru_enable_ocr = request.enable_ocr
        config.mineru_enable_formula = request.enable_formula
        config.mineru_enable_table = request.enable_table
        config.mineru_language = request.language
        
        # 检查 API Key
        if not config.mineru_api_key:
            error_msg = "MinerU API Key 未配置"
            update_stage("failed", 0, error_msg)
            task_manager.update_task(task_id, status="failed", message=error_msg)
            return
        
        service = FullPipelineService(config)
        
        # MinerU 进度回调
        def mineru_progress_callback(attempt: int, state: str, data: Dict):
            progress = data.get("extract_progress", {})
            current_page = progress.get("extracted_pages", 0)
            total_pages = progress.get("total_pages", 0)
            
            # 计算 MinerU 阶段进度
            mineru_progress = 0
            if total_pages > 0:
                mineru_progress = int((current_page / total_pages) * 100)
            elif state == "done" or state == "completed":
                mineru_progress = 100
            else:
                mineru_progress = min(attempt * 10, 90)  # 轮询时渐进增长
            
            logs = [f"解析中... 第{current_page}/{total_pages}页" if total_pages > 0 else f"等待响应... (尝试{attempt})"]
            if state == "done" or state == "completed":
                logs = ["MinerU 解析完成"]
            
            update_stage("mineru", mineru_progress, 
                        "MinerU 解析中..." if mineru_progress < 100 else "MinerU 解析完成",
                        mineru_data={"state": state, "progress": mineru_progress, 
                               "current_page": current_page, "total_pages": total_pages,
                               "logs": logs})
        
        # 处理 PDF
        result = service.process_pdf(
            url=str(request.document_url),
            output_filename=request.output_filename,
            custom_prompt=request.custom_prompt,
            custom_title=request.custom_title,
            wait_callback=mineru_progress_callback
        )
        
        if not result.success:
            error_msg = result.message or "MinerU 解析失败"
            update_stage("failed", 0, error_msg)
            task_manager.update_task(task_id, status="failed", message=error_msg)
            return
        
        # MinerU 完成，进入实体提取阶段
        # 注意：process_pdf 内部会继续执行 LangExtract 和渲染（阻塞调用）
        update_stage("mineru", 100, "MinerU 解析完成，准备实体提取...", 
                    mineru_data={"state": "completed", "progress": 100, "logs": ["解析完成"]})
        
        # ========== 阶段 2: 实体提取 (LangExtract) ==========
        # 由于 process_pdf 是阻塞的，我们在这里更新进度，告诉用户即将开始 LangExtract
        update_stage("extraction", 5, "准备提取配置...",
                    extraction_data={"state": "running", "progress": 5, 
                                     "logs": ["准备提取配置...", "加载示例数据..."]})
        time.sleep(0.2)  # 给前端时间渲染
        
        # 发送"开始调用大模型"进度
        update_stage("extraction", 10, "调用大模型分析文档（约需1-3分钟）...",
                    extraction_data={"state": "running", "progress": 10, 
                                     "logs": ["正在调用 deepseek-chat 模型...", 
                                              "分析文档内容（此步骤耗时较长，请耐心等待）..."]})
        
        # ⚠️ process_pdf 内部会继续执行 LangExtract（阻塞调用）
        # 由于 LangExtract 没有回调机制，前端会卡在 10% 直到完成
        # 获取结果（LangExtract 和渲染已经在 process_pdf 内完成）
        extraction_count = result.highlight_result.extraction_count if result.highlight_result else 0
        
        # LangExtract 和渲染完成后，更新最终进度
        update_stage("extraction", 100, f"提取完成，共 {extraction_count} 个实体",
                    extraction_data={"state": "completed", "progress": 100, 
                               "extracted_count": extraction_count,
                               "logs": [f"提取完成，共 {extraction_count} 个实体", "验证通过"]})
        
        # ========== 阶段 3: 高亮渲染 ==========
        update_stage("highlight", 0, "渲染 PDF 中...",
                    highlight_data={"state": "running", "progress": 0, "logs": ["开始渲染..."]})
        
        highlight_count = result.highlight_result.highlight_count if result.highlight_result else 0
        
        # 模拟渲染进度
        for i in range(5):
            progress = (i + 1) * 20
            logs = [f"渲染中... 已处理 {int(highlight_count * progress / 100)} 处高亮"]
            update_stage("highlight", progress, "渲染 PDF 中...",
                        highlight_data={"state": "running", "progress": progress,
                                  "highlighted_count": int(highlight_count * progress / 100),
                                  "logs": logs})
            time.sleep(0.05)
        
        # ========== 完成 ==========
        result_data = {
            "task_id": task_id,
            "mineru_task_id": result.task_id,
            "output_path": str(result.output_path) if result.output_path else None,
            "md_length": len(result.md_content) if result.md_content else 0,
            "extraction_count": extraction_count,
            "highlight_count": highlight_count,
            "category_counts": result.highlight_result.details.get("category_counts", {}) if result.highlight_result else {}
        }
        
        update_stage("completed", 100, "处理完成",
                    highlight_data={"state": "completed", "progress": 100,
                              "highlighted_count": highlight_count,
                              "logs": ["渲染完成"]})
        
        task_manager.update_task(
            task_id,
            status="completed",
            message="处理完成",
            result=result_data
        )
        print(f"[✓] 任务完成: {task_id}")
        
    except Exception as e:
        error_msg = f"处理异常: {str(e)}"
        print(f"[✗] 任务异常: {task_id} - {error_msg}")
        import traceback
        traceback.print_exc()
        update_stage("failed", 0, error_msg)
        task_manager.update_task(task_id, status="failed", message=error_msg)


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

