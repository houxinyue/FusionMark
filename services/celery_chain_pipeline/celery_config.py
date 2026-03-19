"""
Celery 配置 - 全异步工作流架构

支持 Redis Broker 和 Result Backend，用于 Celery Chain 任务编排

启动 Worker:
    celery -A celery_chain_pipeline.celery_config worker --loglevel=info -Q pdf_processing

监控 Flower:
    celery -A celery_chain_pipeline.celery_config flower --port=5555
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# 从环境变量读取 Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建 Celery 应用
celery_app = Celery(
    "celery_chain_pipeline",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "celery_chain_pipeline.celery_tasks",
    ]
)

# Celery 配置
celery_app.conf.update(
    # 序列化配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务队列配置
    task_queues=(
        Queue("pdf_processing", Exchange("pdf_processing"), routing_key="pdf.process"),
        Queue("mineru", Exchange("mineru"), routing_key="mineru.process"),
        Queue("extraction", Exchange("extraction"), routing_key="extraction.process"),
        Queue("highlight", Exchange("highlight"), routing_key="highlight.process"),
        Queue("default", Exchange("default"), routing_key="default"),
    ),
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # 任务路由 - 每个步骤可以路由到不同队列
    task_routes={
        "celery_chain_pipeline.celery_tasks.step1_mineru_parse": {
            "queue": "mineru",
            "routing_key": "mineru.process"
        },
        "celery_chain_pipeline.celery_tasks.step2_langextract": {
            "queue": "extraction",
            "routing_key": "extraction.process"
        },
        "celery_chain_pipeline.celery_tasks.step3_highlight_render": {
            "queue": "highlight",
            "routing_key": "highlight.process"
        },
    },
    
    # 结果过期时间 (7天)
    result_expires=604800,
    
    # 任务执行时间限制
    task_time_limit=3600,      # 硬限制 60分钟
    task_soft_time_limit=3300, # 软限制 55分钟
    
    # Worker 配置
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    
    # 任务确认方式 - 尽早确认，支持重试
    task_acks_on_failure_or_timeout=False,
    task_reject_on_worker_lost=True,
    
    # 结果后端配置
    result_backend=REDIS_URL,
    result_extended=True,
    result_backend_always_retry=True,
    
    # 重试配置
    task_always_retry=False,
    task_default_retry_delay=60,  # 默认60秒后重试
    task_max_retries=3,
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Redis 连接池配置
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_retry=True,
    
    # 结果后端连接池
    redis_socket_keepalive=True,
    redis_socket_connect_timeout=30,
    redis_retry_on_timeout=True,
)


def get_celery_app():
    """获取 Celery 应用实例"""
    return celery_app


if __name__ == "__main__":
    celery_app.start()
