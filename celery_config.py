"""
Celery 配置 - 分布式任务队列

用于处理大文件和批量 PDF 处理任务

启动 Worker:
    celery -A celery_config worker --loglevel=info -Q pdf_processing

启动 Beat (定时任务):
    celery -A celery_config beat --loglevel=info

监控 Flower:
    celery -A celery_config flower --port=5555
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建 Celery 应用
celery_app = Celery(
    "pdf_processor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["celery_tasks"]  # 任务模块
)

# 配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务队列配置
    task_queues=(
        Queue("pdf_processing", Exchange("pdf_processing"), routing_key="pdf.process"),
        Queue("default", Exchange("default"), routing_key="default"),
    ),
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # 任务路由
    task_routes={
        "celery_tasks.process_pdf": {"queue": "pdf_processing", "routing_key": "pdf.process"},
        "celery_tasks.process_pdf_batch": {"queue": "pdf_processing", "routing_key": "pdf.process"},
    },
    
    # 结果过期时间 (1天)
    result_expires=86400,
    
    # 任务执行时间限制 (30分钟)
    task_time_limit=1800,
    
    # 任务软时间限制 (25分钟)
    task_soft_time_limit=1500,
    
    # Worker 并发数
    worker_concurrency=4,
    
    # 每个 Worker 预取任务数
    worker_prefetch_multiplier=1,
    
    # 任务确认方式
    task_acknowledgments="early",
    
    # 结果后端配置
    result_backend=REDIS_URL,
    result_extended=True,
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)


def get_celery_app():
    """获取 Celery 应用实例"""
    return celery_app


if __name__ == "__main__":
    celery_app.start()
