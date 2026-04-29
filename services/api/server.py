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
    pip install fastapi uvicorn websockets redis

需要先启动 Redis:
    redis-server
"""

import os
import json
import asyncio
import yaml
import shutil
import re
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File, Query, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

try:
    # 从项目根目录运行时
    from services.core.full_pipeline import FullPipelineService, FullPipelineConfig, PipelineResult
    from services.api.progress_store import get_progress_store
    from services.api.websocket_handler import get_websocket_handler
    from services.api.task_processor import process_pdf_task
except ModuleNotFoundError:
    # 从 services 目录内运行时，使用相对导入
    from ..core.full_pipeline import FullPipelineService, FullPipelineConfig, PipelineResult
    from .progress_store import get_progress_store
    from .websocket_handler import get_websocket_handler
    from .task_processor import process_pdf_task

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
        allowed_prefixes = ('http://', 'https://', 'storage://', 'object://', 'minio://', 'file://', 'local://')
        if not v.startswith(allowed_prefixes):
            candidate_path = Path(v).expanduser()
            if not candidate_path.exists():
                raise ValueError('文档输入必须是 http(s) URL、storage:// 对象 key 或已存在的本地文件')
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


SUPPORTED_UPLOAD_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg", ".html", ".htm"
}
MAX_UPLOAD_BYTES = int(os.getenv("TASK_UPLOAD_MAX_BYTES", str(100 * 1024 * 1024)))
UPLOAD_CHUNK_SIZE = 1024 * 1024


def _get_effective_pipeline_config() -> FullPipelineConfig:
    """Load active profile config or default config for request-time checks."""
    config, _ = get_current_profile_config()
    return config or FullPipelineConfig()


def _safe_upload_filename(filename: Optional[str]) -> str:
    """Return a storage-key-safe filename while preserving the extension."""
    raw = Path(filename or "document").name.strip()
    if not raw:
        raw = "document"
    stem = Path(raw).stem or "document"
    suffix = Path(raw).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "document"
    return f"{safe_stem}{suffix}"


def _validate_upload_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Unsupported upload file type: {suffix}. Supported: {supported}")


async def _persist_upload_file(task_id: str, file: UploadFile) -> str:
    """Persist an uploaded file through Storage Provider and return storage:// source."""
    try:
        from services.storage import get_storage_provider
        from services.storage.workspace import get_workspace_dir
    except ModuleNotFoundError:
        from ..storage import get_storage_provider
        from ..storage.workspace import get_workspace_dir

    safe_filename = _safe_upload_filename(file.filename)
    _validate_upload_filename(safe_filename)

    upload_dir = get_workspace_dir(task_id) / "upload"
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / safe_filename

    total = 0
    with open(temp_path, "wb") as out:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail=f"Upload file exceeds {MAX_UPLOAD_BYTES} bytes")
            out.write(chunk)

    if total == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    key = f"tasks/{task_id}/input/{safe_filename}"
    try:
        get_storage_provider().save_file(
            key,
            str(temp_path),
            metadata={
                "task_id": task_id,
                "original_filename": file.filename or safe_filename,
                "source": "task_upload",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist uploaded file: {exc}") from exc

    return f"storage://{key}"


def _schedule_task_processing(
    background_tasks: BackgroundTasks,
    task_id: str,
    document_source: str,
    model: str,
    enable_ocr: bool,
    enable_formula: bool,
    enable_table: bool,
    language: str,
    output_filename: Optional[str],
    custom_title: Optional[str],
    custom_prompt: Optional[str],
) -> TaskResponse:
    store = get_task_store()
    store.create_task(task_id, document_source)

    background_tasks.add_task(
        process_pdf_task,
        task_id=task_id,
        document_url=document_source,
        model=model,
        enable_ocr=enable_ocr,
        enable_formula=enable_formula,
        enable_table=enable_table,
        language=language,
        output_filename=output_filename,
        custom_title=custom_title,
        custom_prompt=custom_prompt,
    )

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="任务已提交，正在处理中",
        created_at=datetime.now().isoformat(),
    )


class ProfileInfo(BaseModel):
    """配置档案信息"""
    name: str
    filename: str
    description: Optional[str] = None
    size: int
    created_at: str
    updated_at: str
    is_current: bool = False


# ============ Redis 进度存储 ============
# 使用 Redis 替代内存存储，支持持久化和 WebSocket 实时推送
# 详见: progress_store.py, websocket_handler.py

def get_task_store():
    """获取任务存储实例"""
    return get_progress_store()

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
            "upload_task": "POST /api/v1/tasks/upload",
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
    task_id = str(uuid.uuid4())
    
    # Create the task record and enqueue background processing.
    return _schedule_task_processing(
        background_tasks=background_tasks,
        task_id=task_id,
        document_source=str(request.document_url),
        model=request.model,
        enable_ocr=request.enable_ocr,
        enable_formula=request.enable_formula,
        enable_table=request.enable_table,
        language=request.language,
        output_filename=request.output_filename,
        custom_title=request.custom_title,
        custom_prompt=request.custom_prompt,
    )


@app.post("/api/v1/tasks/upload", response_model=TaskResponse)
async def submit_upload_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to parse"),
    output_filename: Optional[str] = Form(None),
    custom_title: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    model: str = Form("vlm"),
    enable_ocr: bool = Form(True),
    enable_formula: bool = Form(True),
    enable_table: bool = Form(True),
    language: str = Form("ch"),
):
    """
    Submit a document-processing task from a multipart file upload.

    Uploaded files are persisted through the active Storage Provider and then
    processed via a storage:// input source. This route requires open_sdk mode.
    """
    config = _get_effective_pipeline_config()
    if (config.mineru_client_mode or "").lower() != "open_sdk":
        raise HTTPException(
            status_code=400,
            detail="Uploaded-file tasks require MINERU_CLIENT_MODE=open_sdk",
        )

    task_id = str(uuid.uuid4())
    document_source = await _persist_upload_file(task_id, file)

    return _schedule_task_processing(
        background_tasks=background_tasks,
        task_id=task_id,
        document_source=document_source,
        model=model,
        enable_ocr=enable_ocr,
        enable_formula=enable_formula,
        enable_table=enable_table,
        language=language,
        output_filename=output_filename,
        custom_title=custom_title,
        custom_prompt=custom_prompt,
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询任务状态"""
    store = get_task_store()
    task = store.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 构建进度数据结构（兼容前端格式）
    progress = {
        "stage": task.get("stage", "pending"),
        "stage_progress": task.get("stage_progress", 0),
        "overall_progress": task.get("overall_progress", 0),
        "mineru": task.get("mineru", {"state": "pending", "progress": 0}),
        "extraction": task.get("extraction", {"state": "pending", "progress": 0}),
        "highlight": task.get("highlight", {"state": "pending", "progress": 0})
    }
    
    result = task.get("result")
    if not isinstance(result, dict):
        result = None
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=progress,
        message=task.get("message"),
        result=result
    )


@app.get("/api/v1/tasks")
async def list_tasks(limit: int = 10, offset: int = 0):
    """列出最近任务"""
    store = get_task_store()
    tasks = store.list_tasks(limit=limit + offset)
    
    return {
        "total": len(tasks),
        "limit": limit,
        "offset": offset,
        "tasks": tasks[offset:offset + limit]
    }


@app.get("/api/v1/tasks/{task_id}/download")
async def download_result(task_id: str):
    """下载处理结果 PDF"""
    store = get_task_store()
    task = store.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    result = task.get("result", {})
    if isinstance(result, dict):
        output_path = result.get("output_path")
    else:
        # 兼容字符串存储的结果
        try:
            result = json.loads(result) if isinstance(result, str) else {}
            output_path = result.get("output_path")
        except:
            output_path = None

    # 优先本地文件
    if output_path and Path(output_path).exists():
        return FileResponse(
            path=output_path,
            filename=Path(output_path).name,
            media_type="application/pdf"
        )

    # 本地缺失时回退到 storage provider
    objects = result.get("objects", {}) if isinstance(result, dict) else {}
    highlight_obj = objects.get("highlight_pdf") if isinstance(objects, dict) else None

    if highlight_obj and isinstance(highlight_obj, dict) and highlight_obj.get("key"):
        try:
            from services.storage import get_storage_provider
            provider = get_storage_provider()
            key = highlight_obj["key"]
            data = provider.read_bytes(key)
            if data:
                from io import BytesIO
                filename = highlight_obj.get("key", "").split("/")[-1] or "result.pdf"
                return StreamingResponse(
                    BytesIO(data),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                )
        except Exception as e:
            print(f"[!] 从 storage provider 读取结果失败: {e}")

    raise HTTPException(status_code=404, detail="结果文件不存在")


@app.get("/api/v1/tasks/{task_id}/artifacts/{artifact_type}")
async def get_task_artifact(task_id: str, artifact_type: str):
    """
    从 Storage Provider 按需读取任务产物

    支持的 artifact_type:
        - langextract_html: LangExtract HTML 可视化
        - entities: 结构化提取结果 (JSONL)
        - highlight_pdf: 高亮 PDF

    产物不再全部存入 Redis，减轻 Redis payload，前端按需要拉取。
    """
    store = get_task_store()
    task = store.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    result = task.get("result", {})
    if not isinstance(result, dict):
        try:
            result = json.loads(result) if isinstance(result, str) else {}
        except:
            result = {}

    objects = result.get("objects", {})
    if not isinstance(objects, dict):
        raise HTTPException(status_code=404, detail="任务产物未找到")

    from services.storage import get_storage_provider
    provider = get_storage_provider()

    key: Optional[str] = None
    content_type: str = "application/octet-stream"
    filename: str = "artifact"

    # 根据 artifact_type 定位 storage key
    if artifact_type == "langextract_html":
        langextract = objects.get("langextract")
        if langextract and isinstance(langextract, dict):
            for obj in langextract.get("objects", []):
                if isinstance(obj, dict) and obj.get("key", "").endswith(".html"):
                    key = obj["key"]
                    content_type = "text/html"
                    filename = key.split("/")[-1] or "langextract.html"
                    break
        if not key:
            raise HTTPException(status_code=404, detail="LangExtract HTML 产物未找到")

    elif artifact_type == "entities":
        langextract = objects.get("langextract")
        if langextract and isinstance(langextract, dict):
            for obj in langextract.get("objects", []):
                if isinstance(obj, dict) and obj.get("key", "").endswith(".jsonl"):
                    key = obj["key"]
                    content_type = "application/json"  # 前端按 JSON 数组处理，实际为 JSONL
                    filename = key.split("/")[-1] or "extractions.jsonl"
                    break
        if not key:
            raise HTTPException(status_code=404, detail="Entities 产物未找到")

    elif artifact_type == "highlight_pdf":
        highlight_obj = objects.get("highlight_pdf")
        if highlight_obj and isinstance(highlight_obj, dict) and highlight_obj.get("key"):
            key = highlight_obj["key"]
            content_type = "application/pdf"
            filename = key.split("/")[-1] or "result.pdf"
        if not key:
            raise HTTPException(status_code=404, detail="Highlight PDF 未找到")

    else:
        raise HTTPException(status_code=400, detail=f"不支持的产物类型: {artifact_type}")

    # 从 storage provider 读取内容
    data = provider.read_bytes(key)
    if data is None:
        raise HTTPException(status_code=404, detail="产物内容读取失败")

    from io import BytesIO
    return StreamingResponse(
        BytesIO(data),
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
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


# ============ WebSocket 实时进度 ============
# 使用 Redis PubSub 实现多客户端实时进度同步

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 实时进度推送
    
    使用 Redis PubSub 实现：
    - 多客户端可同时订阅同一任务进度
    - 后台任务更新进度时，所有客户端实时收到推送
    - 支持服务重启后恢复进度查看
    """
    handler = get_websocket_handler()
    store = get_task_store()
    
    await handler.handle(websocket, task_id, store)


# ============ 后台任务处理 ============
# 注意: process_pdf_task 已移动到 task_processor.py
# from .task_processor import process_pdf_task


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    store = get_task_store()
    
    # 统计任务状态
    tasks = store.list_tasks(limit=1000)
    task_stats = {
        "total": len(tasks),
        "pending": sum(1 for t in tasks if t.get("status") == "pending"),
        "processing": sum(1 for t in tasks if t.get("status") == "processing"),
        "completed": sum(1 for t in tasks if t.get("status") == "completed"),
        "failed": sum(1 for t in tasks if t.get("status") == "failed"),
    }
    
    # 检查 Redis 连接
    redis_status = "connected" if store.ping() else "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis": redis_status,
        "tasks": task_stats
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

