"""
Celery 任务定义 - PDF 处理任务

任务列表:
- process_pdf: 处理单个 PDF
- process_pdf_batch: 批量处理 PDF
- cleanup_old_files: 清理过期文件
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from celery import shared_task, Task, current_task
from celery.exceptions import SoftTimeLimitExceeded

from services.core.full_pipeline import FullPipelineService, FullPipelineConfig, PipelineResult
from services.legacy.celery_config import celery_app


class PDFProcessTask(Task):
    """自定义任务基�?""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        print(f"任务 {task_id} 失败: {exc}")
        # 可以在这里发送告警通知
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        print(f"任务 {task_id} 成功完成")


def update_task_progress(task_id: str, progress: Dict[str, Any]):
    """更新任务进度�?Celery 结果后端"""
    if current_task:
        current_task.update_state(
            state="PROGRESS",
            meta={
                "task_id": task_id,
                "progress": progress,
                "timestamp": datetime.now().isoformat()
            }
        )


@shared_task(
    bind=True,
    base=PDFProcessTask,
    name="celery_tasks.process_pdf",
    queue="pdf_processing",
    max_retries=3,
    default_retry_delay=60
)
def process_pdf(
    self,
    pdf_url: str,
    task_id: str,
    config: Optional[Dict[str, Any]] = None,
    output_filename: Optional[str] = None,
    custom_title: Optional[str] = None,
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理单个 PDF 任务
    
    Args:
        pdf_url: PDF 文件 URL
        task_id: 任务 ID
        config: 服务配置字典
        output_filename: 输出文件�?
        custom_title: 自定义标�?
        custom_prompt: 自定义提示词
    
    Returns:
        处理结果字典
    """
    print(f"[{task_id}] 开始处�?PDF: {pdf_url}")
    
    try:
        # 更新状态为开�?
        update_task_progress(task_id, {
            "stage": "mineru",
            "state": "starting",
            "message": "开�?MinerU 解析"
        })
        
        # 创建服务配置
        if config:
            service_config = FullPipelineConfig.from_dict(config)
        else:
            service_config = FullPipelineConfig()
        
        service = FullPipelineService(service_config)
        
        # 定义进度回调
        def progress_callback(stage: str, state: str, progress_data: Dict):
            update_task_progress(task_id, {
                "stage": stage,
                "state": state,
                **progress_data
            })
        
        # 处理 PDF
        result = service.process_pdf(
            url=pdf_url,
            output_filename=output_filename,
            custom_title=custom_title,
            custom_prompt=custom_prompt
        )
        
        if result.success:
            result_data = {
                "success": True,
                "task_id": result.task_id,
                "output_path": str(result.output_path) if result.output_path else None,
                "md_length": len(result.md_content) if result.md_content else 0,
                "extraction_count": result.highlight_result.extraction_count if result.highlight_result else 0,
                "highlight_count": result.highlight_result.highlight_count if result.highlight_result else 0,
                "category_counts": result.highlight_result.details.get("category_counts", {}) if result.highlight_result else {},
                "completed_at": datetime.now().isoformat()
            }
            print(f"[{task_id}] 处理成功: {result_data['output_path']}")
            return result_data
        else:
            error_msg = result.message
            print(f"[{task_id}] 处理失败: {error_msg}")
            
            # 重试逻辑
            if self.request.retries < self.max_retries:
                print(f"[{task_id}] 将在 {self.default_retry_delay} 秒后重试...")
                raise self.retry(exc=Exception(error_msg))
            
            return {
                "success": False,
                "task_id": task_id,
                "error": error_msg,
                "completed_at": datetime.now().isoformat()
            }
    
    except SoftTimeLimitExceeded:
        error_msg = "任务执行超时"
        print(f"[{task_id}] {error_msg}")
        return {
            "success": False,
            "task_id": task_id,
            "error": error_msg,
            "completed_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[{task_id}] 异常: {error_msg}")
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "task_id": task_id,
            "error": error_msg,
            "completed_at": datetime.now().isoformat()
        }


@shared_task(
    bind=True,
    base=PDFProcessTask,
    name="celery_tasks.process_pdf_batch",
    queue="pdf_processing"
)
def process_pdf_batch(
    self,
    pdf_urls: List[str],
    batch_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    批量处理 PDF 任务
    
    Args:
        pdf_urls: PDF URL 列表
        batch_id: 批次 ID
        config: 服务配置
    
    Returns:
        批次处理结果
    """
    print(f"[批次 {batch_id}] 开始批量处理，�?{len(pdf_urls)} 个文�?)
    
    results = []
    success_count = 0
    failed_count = 0
    
    for i, pdf_url in enumerate(pdf_urls):
        # 更新进度
        progress = {
            "current": i + 1,
            "total": len(pdf_urls),
            "current_url": pdf_url,
            "success_count": success_count,
            "failed_count": failed_count
        }
        update_task_progress(batch_id, progress)
        
        # 处理单个文件
        task_id = f"{batch_id}_{i}"
        result = process_pdf.delay(
            pdf_url=pdf_url,
            task_id=task_id,
            config=config
        )
        
        # 等待结果（非阻塞�?
        try:
            task_result = result.get(timeout=1800)  # 最多等�?0分钟
            results.append(task_result)
            
            if task_result.get("success"):
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"[批次 {batch_id}] 文件 {pdf_url} 处理异常: {e}")
            failed_count += 1
            results.append({
                "success": False,
                "url": pdf_url,
                "error": str(e)
            })
    
    batch_result = {
        "batch_id": batch_id,
        "total": len(pdf_urls),
        "success": success_count,
        "failed": failed_count,
        "results": results,
        "completed_at": datetime.now().isoformat()
    }
    
    print(f"[批次 {batch_id}] 批量处理完成: 成功 {success_count}/{len(pdf_urls)}")
    return batch_result


@shared_task(
    name="celery_tasks.cleanup_old_files",
    bind=True
)
def cleanup_old_files(days: int = 7) -> Dict[str, Any]:
    """
    清理过期文件
    
    Args:
        days: 文件保留天数
    
    Returns:
        清理结果
    """
    from services.core.full_pipeline import FullPipelineConfig
    
    config = FullPipelineConfig()
    output_dir = Path(config.final_output_dir)
    mineru_dir = Path(config.mineru_output_dir)
    
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_files = []
    
    # 清理高亮输出目录
    if output_dir.exists():
        for file_path in output_dir.glob("*.pdf"):
            try:
                stat = file_path.stat()
                file_mtime = datetime.fromtimestamp(stat.st_mtime)
                
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    deleted_files.append(str(file_path))
                    print(f"已删除过期文�? {file_path}")
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")
    
    # 清理 MinerU 输出目录
    if mineru_dir.exists():
        for item in mineru_dir.iterdir():
            try:
                stat = item.stat()
                item_mtime = datetime.fromtimestamp(stat.st_mtime)
                
                if item_mtime < cutoff_date:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                    deleted_files.append(str(item))
                    print(f"已删除过期项�? {item}")
            except Exception as e:
                print(f"删除项目失败 {item}: {e}")
    
    result = {
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files,
        "retention_days": days,
        "executed_at": datetime.now().isoformat()
    }
    
    print(f"清理完成: 删除 {len(deleted_files)} 个过期文�?)
    return result


@shared_task(
    name="celery_tasks.get_task_status",
    bind=False
)
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    查询 Celery 任务状�?
    
    Args:
        task_id: Celery 任务 ID
    
    Returns:
        任务状态信�?
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    status_data = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }
    
    if result.ready():
        if result.successful():
            status_data["result"] = result.result
        elif result.failed():
            status_data["error"] = str(result.result)
    else:
        # 获取进度信息
        info = result.info
        if info and isinstance(info, dict):
            status_data["progress"] = info.get("progress", {})
    
    return status_data


# ============ 定时任务配置 ============

celery_app.conf.beat_schedule = {
    "cleanup-old-files-daily": {
        "task": "celery_tasks.cleanup_old_files",
        "schedule": timedelta(days=1),  # 每天执行
        "args": (7,),  # 保留7�?
    },
}


if __name__ == "__main__":
    # 测试任务
    result = process_pdf.delay(
        pdf_url="https://example.com/test.pdf",
        task_id="test_task"
    )
    print(f"任务已提�? {result.id}")
