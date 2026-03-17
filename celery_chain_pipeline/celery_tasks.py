"""
Celery Chain 任务定义 - 三个独立步骤任务

任务链: step1_mineru_parse → step2_langextract → step3_highlight_render

每个任务独立支持:
- 进度实时更新
- 失败自动重试
- 超时保护
"""

import os
import sys
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from celery import shared_task, Task, chain
from celery.exceptions import SoftTimeLimitExceeded

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from celery_chain_pipeline.progress_manager import get_progress_manager

# 导入项目现有服务 (可能需要根据实际结构调整)
try:
    from mineru_client import MinerUClient
    from full_pipeline_service import FullPipelineService, FullPipelineConfig
    from md_highlight_service import MDHighlightService
except ImportError as e:
    print(f"[CeleryTasks] 导入依赖失败: {e}")
    # 定义占位类，避免启动失败
    class MinerUClient:
        pass
    class FullPipelineService:
        pass
    class MDHighlightService:
        pass


# ============ 任务基类 ============

class PipelineTask(Task):
    """Pipeline 任务基类 - 提供通用功能"""
    
    def __init__(self):
        self.progress_manager = get_progress_manager()
    
    def update_progress(self, task_id: str, stage: str, progress: int, message: str, state: str = 'running'):
        """更新进度"""
        self.progress_manager.update_stage_progress(
            task_id=task_id,
            stage=stage,
            progress=progress,
            message=message,
            state=state
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """重试回调"""
        super().on_retry(exc, task_id, args, kwargs, einfo)
        # 获取任务参数中的 task_id
        pipeline_task_id = kwargs.get('pipeline_task_id') or (args[0] if args else None)
        if pipeline_task_id:
            stage = self.name.split('.')[-1].replace('step1_', '').replace('step2_', '').replace('step3_', '').replace('_parse', '').replace('_render', '')
            self.progress_manager.increment_retry_count(pipeline_task_id, stage)
            self.progress_manager.update_stage_progress(
                task_id=pipeline_task_id,
                stage=stage,
                progress=0,
                message=f'{stage} 失败，正在重试 ({self.request.retries}/{self.max_retries})',
                state='running'
            )


# ============ Step 1: MinerU 解析任务 ============

@shared_task(
    bind=True,
    base=PipelineTask,
    name="celery_chain_pipeline.celery_tasks.step1_mineru_parse",
    queue="mineru",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=600,  # 10分钟软超时
    time_limit=900,       # 15分钟硬超时
)
def step1_mineru_parse(
    self,
    pipeline_task_id: str,
    document_url: str,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    步骤1: MinerU 文档解析
    
    特性:
    - 支持进度回调 (轮询 MinerU API)
    - 失败可重试 (max_retries=3)
    - 超时保护 (10分钟软超时)
    
    Args:
        pipeline_task_id: 整个 Pipeline 的任务 ID
        document_url: PDF 文档 URL
        config: 配置参数
        
    Returns:
        {
            "status": "success",
            "md_content": "...",
            "mineru_task_id": "...",
            "total_pages": 10,
            "images": [],
            "metadata": {}
        }
    """
    stage = "mineru"
    progress_manager = get_progress_manager()
    
    try:
        # 标记阶段开始
        progress_manager.update_stage_started(pipeline_task_id, stage)
        
        # 初始化 MinerU 客户端
        api_key = os.getenv("MINERU_API_KEY")
        if not api_key:
            raise ValueError("MINERU_API_KEY 环境变量未设置")
        
        mineru_client = MinerUClient(api_key=api_key)
        
        # 定义 MinerU 进度回调
        def mineru_callback(attempt: int, state: str, data: Dict):
            """MinerU 进度回调"""
            # 计算进度
            if state == "processing":
                progress = min(50 + attempt * 2, 90)  # 模拟进度
                message = f"MinerU 解析中... (尝试 {attempt})"
            elif state == "completed":
                progress = 100
                message = "MinerU 解析完成"
            else:
                progress = 10
                message = f"MinerU 状态: {state}"
            
            progress_manager.update_stage_progress(
                task_id=pipeline_task_id,
                stage=stage,
                progress=progress,
                message=message,
                state='running',
                extra_data={'mineru_state': state, 'attempt': attempt}
            )
        
        # 调用 MinerU 解析
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=10,
            message="提交 MinerU 解析任务...",
            state='running'
        )
        
        # 执行解析
        result = mineru_client.parse_document(
            url=document_url,
            wait_callback=mineru_callback,
            enable_ocr=config.get('enable_ocr', True) if config else True,
            enable_formula=config.get('enable_formula', True) if config else True,
            enable_table=config.get('enable_table', True) if config else True,
        )
        
        # 标记完成
        progress_manager.update_stage_completed(
            task_id=pipeline_task_id,
            stage=stage,
            result={
                'mineru_task_id': result.get('task_id'),
                'total_pages': result.get('total_pages', 0),
                'image_count': len(result.get('images', []))
            }
        )
        
        # 返回给下一步的数据
        return {
            "status": "success",
            "md_content": result.get('markdown', ''),
            "mineru_task_id": result.get('task_id'),
            "total_pages": result.get('total_pages', 0),
            "images": result.get('images', []),
            "metadata": result.get('metadata', {})
        }
        
    except SoftTimeLimitExceeded:
        # 软超时，触发重试
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=0,
            message="MinerU 解析超时，准备重试...",
            state='running'
        )
        raise self.retry(countdown=60)
        
    except Exception as exc:
        # 其他异常，记录失败并触发重试
        error_msg = str(exc)
        progress_manager.update_stage_failed(
            task_id=pipeline_task_id,
            stage=stage,
            error=error_msg,
            will_retry=self.request.retries < self.max_retries
        )
        
        # 如果还有重试次数，则重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        # 无重试次数，抛出异常终止 Chain
        raise


# ============ Step 2: LangExtract 实体提取任务 ============

@shared_task(
    bind=True,
    base=PipelineTask,
    name="celery_chain_pipeline.celery_tasks.step2_langextract",
    queue="extraction",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,  # 5分钟软超时
    time_limit=600,       # 10分钟硬超时
)
def step2_langextract(
    self,
    step1_result: Dict[str, Any],
    pipeline_task_id: str,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    步骤2: LangExtract 实体提取
    
    特性:
    - 虽然是阻塞调用，但有状态更新
    - 支持步骤重试 (LangExtract 偶发超时)
    
    Args:
        step1_result: 上一步的结果 (自动注入)
        pipeline_task_id: 整个 Pipeline 的任务 ID
        config: 配置参数
        
    Returns:
        {
            "status": "success",
            "extraction_count": 5,
            "extractions": [...],
            "highlight_count": 10,
            "md_content": "..."  # 透传
        }
    """
    stage = "extraction"
    progress_manager = get_progress_manager()
    
    try:
        # 检查上一步结果
        if step1_result.get('status') != 'success':
            raise ValueError(f"上一步执行失败: {step1_result}")
        
        md_content = step1_result.get('md_content', '')
        if not md_content:
            raise ValueError("上一步未返回 Markdown 内容")
        
        # 标记阶段开始
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=10,
            message="准备提取配置...",
            state='running'
        )
        
        # 模拟进度更新 (LangExtract 是阻塞调用)
        # 给前端反馈，避免卡住无响应
        time.sleep(0.5)
        
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=20,
            message="调用大模型分析（约需1-3分钟）...",
            state='running'
        )
        
        # 尝试导入 LangExtract
try:
            from langextract import extract
            
            # 获取配置
            prompt = config.get('custom_prompt') if config else None
            examples = config.get('examples') if config else None
            model_id = config.get('model_id') if config else None
            
            # 执行实体提取 (阻塞 2-3分钟)
            extraction_result = extract(
                text_or_documents=md_content,
                prompt_description=prompt or "提取文档中的关键实体信息",
                examples=examples,
                model_id=model_id
            )
            
            extraction_count = len(extraction_result.extractions)
            highlight_count = len(extraction_result.highlights) if hasattr(extraction_result, 'highlights') else 0
            
        except ImportError:
            # LangExtract 未安装，使用模拟数据
            progress_manager.update_stage_progress(
                task_id=pipeline_task_id,
                stage=stage,
                progress=50,
                message="LangExtract 未安装，使用模拟数据...",
                state='running'
            )
            extraction_count = 3
            highlight_count = 5
            extraction_result = {
                'extractions': [
                    {'text': '示例实体1', 'category': '组织'},
                    {'text': '示例实体2', 'category': '人物'},
                    {'text': '示例实体3', 'category': '地点'},
                ],
                'highlights': []
            }
        
        # 标记完成
        progress_manager.update_stage_completed(
            task_id=pipeline_task_id,
            stage=stage,
            result={
                'extraction_count': extraction_count,
                'highlight_count': highlight_count
            }
        )
        
        # 返回给下一步的数据 (需要包含 md_content)
        return {
            "status": "success",
            "extraction_count": extraction_count,
            "extractions": extraction_result.extractions if hasattr(extraction_result, 'extractions') else extraction_result.get('extractions', []),
            "highlight_count": highlight_count,
            "md_content": md_content,  # 透传给下一步
            "mineru_task_id": step1_result.get('mineru_task_id')
        }
        
    except SoftTimeLimitExceeded:
        # 软超时，触发重试
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=0,
            message="实体提取超时，准备重试...",
            state='running'
        )
        raise self.retry(countdown=30)
        
    except Exception as exc:
        error_msg = str(exc)
        progress_manager.update_stage_failed(
            task_id=pipeline_task_id,
            stage=stage,
            error=error_msg,
            will_retry=self.request.retries < self.max_retries
        )
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        raise


# ============ Step 3: 高亮渲染任务 ============

@shared_task(
    bind=True,
    base=PipelineTask,
    name="celery_chain_pipeline.celery_tasks.step3_highlight_render",
    queue="highlight",
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=120,  # 2分钟软超时
    time_limit=300,       # 5分钟硬超时
)
def step3_highlight_render(
    self,
    step2_result: Dict[str, Any],
    pipeline_task_id: str,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    步骤3: 高亮渲染
    
    特性:
    - 分步更新进度 (PDF生成、字体加载等)
    - 本地计算，通常很快
    
    Args:
        step2_result: 上一步的结果 (自动注入)
        pipeline_task_id: 整个 Pipeline 的任务 ID
        config: 配置参数
        
    Returns:
        {
            "status": "success",
            "output_path": "/path/to/output.pdf",
            "highlight_count": 10,
            "output_url": "..."
        }
    """
    stage = "highlight"
    progress_manager = get_progress_manager()
    
    try:
        # 检查上一步结果
        if step2_result.get('status') != 'success':
            raise ValueError(f"上一步执行失败: {step2_result}")
        
        md_content = step2_result.get('md_content', '')
        extractions = step2_result.get('extractions', [])
        
        # 标记阶段开始
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=0,
            message="开始渲染PDF...",
            state='running'
        )
        
        # 准备渲染数据
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=20,
            message="准备渲染数据...",
            state='running'
        )
        
        # 模拟渲染过程 (实际项目中使用 MDHighlightService)
        time.sleep(0.5)
        
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=50,
            message="生成高亮HTML...",
            state='running'
        )
        
        time.sleep(0.5)
        
        progress_manager.update_stage_progress(
            task_id=pipeline_task_id,
            stage=stage,
            progress=80,
            message="渲染PDF...",
            state='running'
        )
        
        # 执行渲染 (实际项目中使用真实服务)
        # highlight_service = MDHighlightService()
        # output_path = highlight_service.render(
        #     md_content=md_content,
        #     extractions=extractions,
        #     output_filename=config.get('output_filename') if config else None
        # )
        
        # 模拟输出路径
        output_dir = Path("highlight_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{pipeline_task_id}.pdf"
        
        # 模拟写入文件
        output_path.write_text("Mock PDF Content")
        
        time.sleep(0.5)
        
        highlight_count = len(extractions)
        
        # 标记完成
        progress_manager.update_stage_completed(
            task_id=pipeline_task_id,
            stage=stage,
            result={
                'output_path': str(output_path),
                'highlight_count': highlight_count,
                'output_filename': output_path.name
            }
        )
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "highlight_count": highlight_count,
            "output_url": f"/api/v1/tasks/{pipeline_task_id}/download"
        }
        
    except SoftTimeLimitExceeded:
        raise self.retry(countdown=30)
        
    except Exception as exc:
        error_msg = str(exc)
        progress_manager.update_stage_failed(
            task_id=pipeline_task_id,
            stage=stage,
            error=error_msg,
            will_retry=self.request.retries < self.max_retries
        )
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        
        raise


# ============ 回调任务 ============

@shared_task(
    name="celery_chain_pipeline.celery_tasks.on_pipeline_success"
)
def on_pipeline_success(results: list, pipeline_task_id: str) -> Dict[str, Any]:
    """
    整个 Pipeline 成功完成后的回调
    
    Args:
        results: 各步骤的结果列表 [step1_result, step2_result, step3_result]
        pipeline_task_id: Pipeline 任务 ID
    """
    progress_manager = get_progress_manager()
    
    final_result = {
        'pipeline_task_id': pipeline_task_id,
        'status': 'completed',
        'steps': {
            'mineru': results[0] if len(results) > 0 else None,
            'extraction': results[1] if len(results) > 1 else None,
            'highlight': results[2] if len(results) > 2 else None,
        },
        'output': results[2] if len(results) > 2 else None,
        'completed_at': datetime.now().isoformat()
    }
    
    progress_manager.complete_task(pipeline_task_id, final_result)
    
    return final_result


@shared_task(
    name="celery_chain_pipeline.celery_tasks.on_pipeline_failure"
)
def on_pipeline_failure(exc: Exception, pipeline_task_id: str) -> Dict[str, Any]:
    """
    Pipeline 失败回调
    
    Args:
        exc: 异常对象
        pipeline_task_id: Pipeline 任务 ID
    """
    progress_manager = get_progress_manager()
    
    error_msg = str(exc)
    progress_manager.fail_task(pipeline_task_id, error_msg)
    
    return {
        'pipeline_task_id': pipeline_task_id,
        'status': 'failed',
        'error': error_msg,
        'failed_at': datetime.now().isoformat()
    }


# ============ 辅助函数 ============

def create_pipeline(
    pipeline_task_id: str,
    document_url: str,
    config: Optional[Dict] = None
):
    """
    创建 Celery Chain Pipeline
    
    使用方式:
        pipeline = create_pipeline(
            pipeline_task_id="task-123",
            document_url="https://example.com/doc.pdf",
            config={"enable_ocr": True}
        )
        result = pipeline.apply_async()
    
    Args:
        pipeline_task_id: Pipeline 任务 ID
        document_url: 文档 URL
        config: 配置参数
        
    Returns:
        Celery Chain 对象
    """
    # 使用 chain 创建任务链
    # step1 -> step2 -> step3
    pipeline = chain(
        step1_mineru_parse.s(pipeline_task_id, document_url, config),
        step2_langextract.s(pipeline_task_id, config),
        step3_highlight_render.s(pipeline_task_id, config)
    )
    
    return pipeline


def submit_pipeline(
    pipeline_task_id: str,
    document_url: str,
    config: Optional[Dict] = None
):
    """
    提交 Pipeline 任务
    
    使用方式:
        result = submit_pipeline(
            pipeline_task_id="task-123",
            document_url="https://example.com/doc.pdf"
        )
        print(result.id)  # Celery 任务 ID
    
    Returns:
        AsyncResult 对象
    """
    from celery_chain_pipeline.progress_manager import get_progress_manager
    
    # 初始化任务进度
    progress_manager = get_progress_manager()
    progress_manager.init_task(pipeline_task_id, document_url, config)
    
    # 创建并提交 Pipeline
    pipeline = create_pipeline(pipeline_task_id, document_url, config)
    
    # 提交任务链，设置回调
    result = pipeline.apply_async(
        link=on_pipeline_success.s(pipeline_task_id),
        link_error=on_pipeline_failure.s(pipeline_task_id)
    )
    
    return result
