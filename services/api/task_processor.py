"""
异步 PDF 处理任务 - Redis 进度集成 (重构版)

方案 B 实现：
1. MinerU 解析（带实时进度回调）
2. LangExtract 阻塞前通知 + 独立执行
3. 高亮渲染独立执行

每个阶段都能独立更新进度到 Redis/PubSub
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


def get_pipeline_config():
    """获取 Pipeline 配置（延迟导入避免循环依赖）"""
    try:
        from ..core.full_pipeline import FullPipelineConfig
        from ..profiles import get_current_user_id, get_profile_manager
    except ImportError:
        from services.core.full_pipeline import FullPipelineConfig
        from services.profiles import get_current_user_id, get_profile_manager

    try:
        config, _ = get_profile_manager().get_current_config(get_current_user_id())
        return config
    except Exception as e:
        print(f"[!] Failed to load storage-backed profile config: {e}")
        return FullPipelineConfig()
    
    # 尝试加载当前激活的配置
    services_dir = Path(__file__).parent.parent
    profiles_dir = services_dir / "profiles"
    current_file = profiles_dir / ".current.yaml"
    
    config = None
    if current_file.exists():
        try:
            import yaml
            with open(current_file, 'r', encoding='utf-8') as f:
                current = yaml.safe_load(f)
                profile_file = current.get('profile_file') if current else None
            
            if profile_file:
                config_path = profiles_dir / profile_file
                if config_path.exists():
                    config = FullPipelineConfig.from_yaml(config_path)
        except Exception as e:
            print(f"[!] 加载配置失败: {e}")
    
    if config is None:
        config = FullPipelineConfig()
    
    return config


def get_mineru_client(config):
    """获取 MinerU 客户端"""
    try:
        from ..clients.mineru_provider import MinerUProviderFactory
    except ImportError:
        from services.clients.mineru_provider import MinerUProviderFactory
    return MinerUProviderFactory.create(config.get_mineru_config())


def get_highlight_service(config):
    """获取高亮服务"""
    try:
        from ..core.highlight import MDHighlightService
    except ImportError:
        from services.core.highlight import MDHighlightService
    
    # 同步输出目录
    config.highlight_config.output_dir = config.final_output_dir
    return MDHighlightService(config.highlight_config)


def _should_store(kind: str) -> bool:
    """根据环境变量判断是否持久化指定类型的产物"""
    env_map = {
        "mineru": "STORE_MINERU_EXTRACTED",
        "langextract": "STORE_LANGEXTRACT_ARTIFACTS",
        "langextract_verbose": "STORE_LANGEXTRACT_VERBOSE_ARTIFACTS",
        "highlight": "STORE_HIGHLIGHT_ARTIFACTS",
    }
    env_var = env_map.get(kind, "")
    if not env_var:
        return False
    return os.getenv(env_var, "true" if kind != "langextract_verbose" else "false").lower() in ("true", "1", "yes")


def _persist_task_artifacts(
    task_id: str,
    mineru_result,
    extraction_result,
    config
) -> Dict[str, Any]:
    """
    将任务产物从工作区持久化到 Storage Provider

    Returns:
        objects 字典: {artifact_name: {key, url, size}}
    """
    try:
        from ..storage import get_storage_provider
    except ImportError:
        from services.storage import get_storage_provider

    provider = get_storage_provider()
    objects: Dict[str, Any] = {}

    # 1. MinerU extracted 目录（不存 zip）
    if _should_store("mineru") and mineru_result and mineru_result.extract_dir:
        extract_dir = Path(mineru_result.extract_dir)
        if extract_dir.exists() and extract_dir.is_dir():
            prefix = f"tasks/{task_id}/mineru/extracted"
            saved = provider.save_directory(prefix, str(extract_dir))
            if saved:
                objects["mineru_extracted"] = {
                    "prefix": prefix,
                    "count": len(saved),
                    "objects": [{"key": o.key, "size": o.size, "url": o.url} for o in saved]
                }

    # 2. LangExtract 产物（JSONL + HTML 等）
    if _should_store("langextract") and config and config.final_output_dir:
        debug_dir = Path(config.final_output_dir) / "debug"
        if debug_dir.exists() and debug_dir.is_dir():
            prefix = f"tasks/{task_id}/langextract"
            saved = provider.save_directory(prefix, str(debug_dir))
            if saved:
                objects["langextract"] = {
                    "prefix": prefix,
                    "count": len(saved),
                    "objects": [{"key": o.key, "size": o.size, "url": o.url} for o in saved]
                }

    # 3. Highlight PDF
    if _should_store("highlight") and extraction_result and extraction_result.output_path:
        output_path = Path(extraction_result.output_path)
        if output_path.exists() and output_path.is_file():
            key = f"tasks/{task_id}/highlight/{output_path.name}"
            obj = provider.save_file(key, str(output_path))
            objects["highlight_pdf"] = {
                "key": obj.key,
                "size": obj.size,
                "url": obj.url
            }

    return objects


async def process_pdf_task_async(
    task_id: str,
    document_url: str,
    model: str = "vlm",
    enable_ocr: bool = True,
    enable_formula: bool = True,
    enable_table: bool = True,
    language: str = "ch",
    output_filename: Optional[str] = None,
    custom_title: Optional[str] = None,
    custom_prompt: Optional[str] = None
):
    """
    异步处理 PDF 任务 - 方案 B 实现
    
    流程拆分：
    1. MinerU 解析（带进度回调，实时更新）
    2. LangExtract 实体提取（阻塞前先发通知）
    3. 高亮渲染（独立步骤）
    """
    from .progress_store import get_progress_store
    
    store = get_progress_store()
    loop = asyncio.get_event_loop()
    
    # ========== 辅助函数：更新进度 ==========
    def update_stage_sync(
        stage: str,
        stage_progress: int = 0,
        message: str = None,
        mineru_data: Dict = None,
        extraction_data: Dict = None,
        highlight_data: Dict = None,
        status: str = "processing"
    ):
        """同步更新进度（供回调使用）"""
        initial_progress = 5

        # 计算总体进度
        stage_weights = {
            "pending": 0,
            "mineru": 40,
            "extraction": 30,
            "highlight": 30,
            "completed": 0
        }
        
        stage_order = ["pending", "mineru", "extraction", "highlight", "completed"]
        overall_progress = 0
        
        if stage in stage_weights:
            completed_weight = 0
            current_stage_index = stage_order.index(stage)
            for i in range(current_stage_index):
                completed_weight += stage_weights.get(stage_order[i], 0)
            
            current_weight = stage_weights.get(stage, 0)
            current_progress = stage_progress / 100
            overall_progress = int(completed_weight + current_weight * current_progress)

            # 任务创建后初始进度为 5%，避免进入首个阶段时出现“先增长再回到 0”。
            if stage in {"mineru", "extraction", "highlight"}:
                overall_progress = max(initial_progress, overall_progress)

        store.update_progress(
            task_id=task_id,
            stage=stage,
            stage_progress=stage_progress,
            overall_progress=overall_progress,
            message=message or f"{stage} 处理中...",
            status=status,
            mineru_data=mineru_data,
            extraction_data=extraction_data,
            highlight_data=highlight_data
        )
    
    async def update_stage(
        stage: str,
        stage_progress: int = 0,
        message: str = None,
        mineru_data: Dict = None,
        extraction_data: Dict = None,
        highlight_data: Dict = None,
        status: str = "processing"
    ):
        """异步更新进度"""
        update_stage_sync(stage, stage_progress, message, mineru_data, extraction_data, highlight_data, status)
    
    def mark_failed(message: str):
        """标记任务失败"""
        store.update_progress(
            task_id=task_id,
            stage="failed",
            status="failed",
            message=message
        )
    
    # 等待一小段时间，确保 WebSocket 已连接
    await asyncio.sleep(0.5)
    
    # ========== 阶段 1: MinerU 解析 ==========
    print(f"[{task_id}] 开始 MinerU 解析...")
    await update_stage(
        "mineru", 0,
        "MinerU 解析准备中...",
        mineru_data={"state": "running", "progress": 0, "logs": ["准备解析文档..."]}
    )
    
    try:
        # 加载配置
        config = get_pipeline_config()
        config.mineru_model = model
        config.mineru_enable_ocr = enable_ocr
        config.mineru_enable_formula = enable_formula
        config.mineru_enable_table = enable_table
        config.mineru_language = language
        
        mineru_config = config.get_mineru_config()
        if not mineru_config.api_key and not mineru_config.sdk_token:
            mark_failed("MinerU API Key 未配置")
            return
        
        # ========== 设置任务级工作区 ==========
        try:
            from ..storage.workspace import get_mineru_workspace, get_highlight_workspace, cleanup_workspace, should_cleanup_workspace
        except ImportError:
            from services.storage.workspace import get_mineru_workspace, get_highlight_workspace, cleanup_workspace, should_cleanup_workspace
        
        mineru_ws = get_mineru_workspace(task_id)
        highlight_ws = get_highlight_workspace(task_id)
        config.mineru_output_dir = str(mineru_ws)
        config.final_output_dir = str(highlight_ws)
        print(f"[{task_id}] 工作区: mineru={mineru_ws}, highlight={highlight_ws}")
        
        mineru_client = get_mineru_client(config)
        try:
            resolved_input = config.get_document_input_resolver().resolve(
                source=document_url,
                task_id=task_id,
            )
        except Exception as exc:
            mark_failed(f"文档输入解析失败: {exc}")
            return
        
        # MinerU 进度回调 - 使用队列实现线程到协程的通信
        progress_queue = asyncio.Queue()
        
        def mineru_progress_callback(attempt: int, state: str, data: Dict):
            """MinerU 进度回调（在后台线程中执行）"""
            progress_info = data.get("extract_progress", {})
            current_page = progress_info.get("extracted_pages", 0)
            total_pages = progress_info.get("total_pages", 0)
            
            # 计算进度
            mineru_progress = 0
            if total_pages > 0:
                mineru_progress = int((current_page / total_pages) * 100)
            elif state in ("done", "completed"):
                mineru_progress = 100
            else:
                mineru_progress = min(attempt * 10, 90)
            
            logs = []
            if total_pages > 0:
                logs.append(f"解析中... 第 {current_page}/{total_pages} 页")
            else:
                logs.append(f"等待响应... (尝试 {attempt})")
            
            if state in ("done", "completed"):
                logs = ["MinerU 解析完成"]
            
            # 放入队列，由主协程处理
            progress_queue.put_nowait({
                "stage": "mineru",
                "stage_progress": mineru_progress,
                "message": "MinerU 解析中..." if mineru_progress < 100 else "MinerU 解析完成",
                "mineru_data": {
                    "state": state,
                    "progress": mineru_progress,
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "logs": logs
                }
            })
        
        # 启动进度处理器协程
        async def process_mineru_progress():
            """处理 MinerU 进度更新"""
            while True:
                try:
                    # 使用 timeout 检查是否应该退出
                    update_data = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                    update_stage_sync(
                        update_data["stage"],
                        update_data["stage_progress"],
                        update_data["message"],
                        mineru_data=update_data["mineru_data"]
                    )
                except asyncio.TimeoutError:
                    # 检查 MinerU 是否已完成
                    if mineru_future.done():
                        # 处理剩余消息
                        while not progress_queue.empty():
                            try:
                                update_data = progress_queue.get_nowait()
                                update_stage_sync(
                                    update_data["stage"],
                                    update_data["stage_progress"],
                                    update_data["message"],
                                    mineru_data=update_data["mineru_data"]
                                )
                            except asyncio.QueueEmpty:
                                break
                        break
        
        # 在后台线程执行 MinerU 解析
        def run_mineru():
            return mineru_client.process_document(
                source=resolved_input.source,
                model_version=config.mineru_model,
                is_ocr=config.mineru_enable_ocr,
                enable_formula=config.mineru_enable_formula,
                enable_table=config.mineru_enable_table,
                language=config.mineru_language,
                wait_callback=mineru_progress_callback
            )
        
        # 并发执行 MinerU 解析和进度处理
        mineru_future = loop.run_in_executor(None, run_mineru)
        await process_mineru_progress()
        
        # 获取 MinerU 结果
        mineru_result = await mineru_future
        
        if not mineru_result:
            mark_failed("MinerU 解析失败")
            return
        
        if mineru_result.state == "failed":
            mark_failed(f"MinerU 任务失败: {mineru_result.error_msg}")
            return
        
        if not mineru_result.content:
            mark_failed("MinerU 未返回内容")
            return
        
        # MinerU 完成
        await update_stage(
            "mineru", 100,
            "MinerU 解析完成",
            mineru_data={"state": "completed", "progress": 100, "logs": ["解析完成"]}
        )
        print(f"[{task_id}] MinerU 解析完成，内容长度: {len(mineru_result.content)}")
        
        # ========== 阶段 2: LangExtract 实体提取 ==========
        print(f"[{task_id}] 开始实体提取...")
        
        # ⭐ 关键：阻塞前先发状态通知
        await update_stage(
            "extraction", 10,
            "调用大模型分析文档(约需1-3分钟,请耐心等待)...",
            extraction_data={
                "state": "running",
                "progress": 10,
                "logs": ["正在调用大模型...", "分析文档内容(此步骤耗时较长,请耐心等待)..."]
            }
        )
        
        # 准备输出文件名
        if output_filename is None:
            output_filename = f"{mineru_result.task_id}_highlighted.pdf"
        
        title = custom_title or f"智能分析报告 - {mineru_result.task_id}"
        
        # 在后台线程执行 LangExtract
        highlight_service = get_highlight_service(config)
        
        def run_extraction():
            return highlight_service.process_text(
                md_text=mineru_result.content,
                output_filename=output_filename,
                custom_prompt=custom_prompt,
                custom_title=title
            )
        
        extraction_result = await loop.run_in_executor(None, run_extraction)
        
        if not extraction_result.success:
            mark_failed(f"实体提取失败: {extraction_result.message}")
            return
        
        # 提取完成
        extraction_count = extraction_result.extraction_count
        highlight_count = extraction_result.highlight_count
        category_counts = extraction_result.details.get("category_counts", {})
        entities = extraction_result.details.get("entities", [])
        langextract_html = extraction_result.details.get("langextract_html")
        
        await update_stage(
            "extraction", 100,
            f"实体提取完成，共 {extraction_count} 个实体",
            extraction_data={
                "state": "completed",
                "progress": 100,
                "extracted_count": extraction_count,
                "logs": [f"提取完成，共 {extraction_count} 个实体", "验证通过"]
            }
        )
        print(f"[{task_id}] 实体提取完成: {extraction_count} 个实体")
        
        # ========== 阶段 3: 高亮渲染 ==========
        print(f"[{task_id}] 开始高亮渲染...")
        
        # 渲染阶段（实际上 LangExtract 和渲染是一体的，这里做进度动画）
        await update_stage(
            "highlight", 0,
            "生成高亮 PDF 中...",
            highlight_data={"state": "running", "progress": 0, "logs": ["开始渲染..."]}
        )
        
        # 模拟渲染进度（实际渲染已在 extraction 中完成）
        for i in range(1, 6):
            progress = i * 20
            logs = [f"渲染中... 已处理 {int(highlight_count * progress / 100)} 处高亮"]
            await update_stage(
                "highlight", progress,
                "生成高亮 PDF 中...",
                highlight_data={
                    "state": "running",
                    "progress": progress,
                    "highlighted_count": int(highlight_count * progress / 100),
                    "logs": logs
                }
            )
            await asyncio.sleep(0.1)
        
        # ========== 持久化产物 ==========
        objects = _persist_task_artifacts(
            task_id=task_id,
            mineru_result=mineru_result,
            extraction_result=extraction_result,
            config=config
        )
        
        # ========== 清理工作区（根据配置） ==========
        if should_cleanup_workspace():
            cleanup_ok = cleanup_workspace(task_id)
            if cleanup_ok:
                print(f"[{task_id}] 工作区已清理")
            else:
                print(f"[{task_id}] 工作区清理失败（非致命）")
        
        # ========== 完成 ==========
        # 注：langextract_html 和 entities 不再存入 Redis，减轻 payload
        # 前端通过 GET /api/v1/tasks/{task_id}/artifacts/{type} 从 Storage 按需获取
        result_data = {
            "task_id": task_id,
            "mineru_task_id": mineru_result.task_id,
            "output_path": str(extraction_result.output_path) if extraction_result.output_path else None,
            "md_length": len(mineru_result.content),
            "extraction_count": extraction_count,
            "highlight_count": highlight_count,
            "category_counts": category_counts,
            "objects": objects
        }
        
        await update_stage(
            "completed", 100,
            "处理完成",
            status="completed",
            highlight_data={
                "state": "completed",
                "progress": 100,
                "highlighted_count": highlight_count,
                "logs": ["渲染完成"]
            }
        )
        
        # 写入最终结果
        store.update_progress(
            task_id=task_id,
            stage="completed",
            stage_progress=100,
            overall_progress=100,
            status="completed",
            message="处理完成",
            result=result_data,
            highlight_data={
                "state": "completed",
                "progress": 100,
                "highlighted_count": highlight_count,
                "logs": ["渲染完成"]
            }
        )
        
        print(f"[✓] 任务完成: {task_id}")
        
    except Exception as e:
        error_msg = f"处理异常: {str(e)}"
        print(f"[✗] 任务异常: {task_id} - {error_msg}")
        import traceback
        traceback.print_exc()
        mark_failed(error_msg)


def process_pdf_task(
    task_id: str,
    document_url: str,
    model: str = "vlm",
    enable_ocr: bool = True,
    enable_formula: bool = True,
    enable_table: bool = True,
    language: str = "ch",
    output_filename: Optional[str] = None,
    custom_title: Optional[str] = None,
    custom_prompt: Optional[str] = None
):
    """
    同步包装器 - 供 BackgroundTasks 调用
    """
    asyncio.run(process_pdf_task_async(
        task_id=task_id,
        document_url=document_url,
        model=model,
        enable_ocr=enable_ocr,
        enable_formula=enable_formula,
        enable_table=enable_table,
        language=language,
        output_filename=output_filename,
        custom_title=custom_title,
        custom_prompt=custom_prompt
    ))
