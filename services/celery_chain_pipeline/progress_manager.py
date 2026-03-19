"""
统一进度管理器

负责管理 Celery Chain 各步骤的进度数据存储和 WebSocket 推送

使用 Redis 存储:
    - Hash: task:{task_id}:progress - 详细进度数据
    - Hash: task:{task_id}:steps - 各步骤状态
    - Pub/Sub: task:{task_id}:updates - 实时更新通道
"""

import os
import json
import time
import redis
from typing import Dict, Any, Optional
from datetime import datetime


class ProgressManager:
    """统一进度管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, redis_url: Optional[str] = None):
        if self._initialized:
            return
            
        # Redis 连接
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=30,
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # 阶段权重配置 (用于计算总体进度)
        self.stage_weights = {
            'mineru': 40,      # MinerU 解析占 40%
            'extraction': 30,  # 实体提取占 30%
            'highlight': 30    # 高亮渲染占 30%
        }
        
        # 阶段名称映射
        self.stage_names = {
            'mineru': '文档解析',
            'extraction': '实体提取',
            'highlight': '高亮渲染'
        }
        
        self._initialized = True
    
    def _get_progress_key(self, task_id: str) -> str:
        """获取进度数据 Redis Key"""
        return f"task:{task_id}:progress"
    
    def _get_steps_key(self, task_id: str) -> str:
        """获取步骤状态 Redis Key"""
        return f"task:{task_id}:steps"
    
    def _get_channel(self, task_id: str) -> str:
        """获取 Pub/Sub 频道名"""
        return f"task:{task_id}:updates"
    
    def init_task(self, task_id: str, document_url: str, config: Optional[Dict] = None):
        """
        初始化任务进度数据
        
        Args:
            task_id: 任务 ID
            document_url: 文档 URL
            config: 任务配置
        """
        progress_key = self._get_progress_key(task_id)
        steps_key = self._get_steps_key(task_id)
        
        now = datetime.now().isoformat()
        
        # 初始化进度数据
        progress_data = {
            'task_id': task_id,
            'document_url': document_url,
            'status': 'pending',
            'current_stage': None,
            'overall_progress': 0,
            'created_at': now,
            'updated_at': now,
            'config': json.dumps(config) if config else '{}'
        }
        
        # 初始化各步骤状态
        steps_data = {
            'mineru_status': 'pending',
            'mineru_progress': '0',
            'mineru_message': '等待开始',
            'mineru_started_at': '',
            'mineru_completed_at': '',
            'mineru_retries': '0',
            
            'extraction_status': 'pending',
            'extraction_progress': '0',
            'extraction_message': '等待开始',
            'extraction_started_at': '',
            'extraction_completed_at': '',
            'extraction_retries': '0',
            
            'highlight_status': 'pending',
            'highlight_progress': '0',
            'highlight_message': '等待开始',
            'highlight_started_at': '',
            'highlight_completed_at': '',
            'highlight_retries': '0',
        }
        
        self.redis.hset(progress_key, mapping=progress_data)
        self.redis.hset(steps_key, mapping=steps_data)
        
        # 设置过期时间 (7天)
        self.redis.expire(progress_key, 604800)
        self.redis.expire(steps_key, 604800)
        
        # 发布初始化消息
        self._publish_update(task_id, {
            'type': 'init',
            'task_id': task_id,
            'status': 'pending',
            'overall_progress': 0,
            'message': '任务已创建，等待处理'
        })
    
    def update_stage_progress(
        self,
        task_id: str,
        stage: str,
        progress: int,
        message: Optional[str] = None,
        state: str = 'running',
        extra_data: Optional[Dict] = None
    ):
        """
        更新阶段进度
        
        Args:
            task_id: 任务 ID
            stage: 阶段名称 (mineru/extraction/highlight)
            progress: 进度百分比 (0-100)
            message: 状态消息
            state: 状态 (pending/running/completed/failed)
            extra_data: 额外数据
        """
        progress_key = self._get_progress_key(task_id)
        steps_key = self._get_steps_key(task_id)
        
        now = datetime.now().isoformat()
        
        # 更新步骤数据
        step_updates = {
            f'{stage}_status': state,
            f'{stage}_progress': str(progress),
            f'{stage}_message': message or self.stage_names.get(stage, stage),
            f'{stage}_updated_at': now,
        }
        
        # 如果刚开始，记录开始时间
        if state == 'running' and progress == 0:
            step_updates[f'{stage}_started_at'] = now
        
        # 如果完成或失败，记录完成时间
        if state in ('completed', 'failed'):
            step_updates[f'{stage}_completed_at'] = now
        
        self.redis.hset(steps_key, mapping=step_updates)
        
        # 更新总体进度数据
        overall_progress = self._calculate_overall_progress(task_id)
        
        progress_updates = {
            'current_stage': stage,
            'overall_progress': str(overall_progress),
            'updated_at': now,
        }
        
        if state == 'failed':
            progress_updates['status'] = 'failed'
        elif state == 'completed' and overall_progress >= 100:
            progress_updates['status'] = 'completed'
        else:
            progress_updates['status'] = 'processing'
        
        self.redis.hset(progress_key, mapping=progress_updates)
        
        # 发布更新
        update_data = {
            'type': 'progress',
            'task_id': task_id,
            'stage': stage,
            'stage_name': self.stage_names.get(stage, stage),
            'stage_progress': progress,
            'overall_progress': overall_progress,
            'state': state,
            'message': message or '',
            'timestamp': now
        }
        
        if extra_data:
            update_data['extra'] = extra_data
        
        self._publish_update(task_id, update_data)
        
        return overall_progress
    
    def update_stage_started(self, task_id: str, stage: str):
        """标记阶段开始"""
        return self.update_stage_progress(
            task_id=task_id,
            stage=stage,
            progress=0,
            message=f'开始{self.stage_names.get(stage, stage)}...',
            state='running'
        )
    
    def update_stage_completed(self, task_id: str, stage: str, result: Optional[Dict] = None):
        """标记阶段完成"""
        return self.update_stage_progress(
            task_id=task_id,
            stage=stage,
            progress=100,
            message=f'{self.stage_names.get(stage, stage)}完成',
            state='completed',
            extra_data=result
        )
    
    def update_stage_failed(self, task_id: str, stage: str, error: str, will_retry: bool = False):
        """标记阶段失败"""
        message = f'{self.stage_names.get(stage, stage)}失败: {error}'
        if will_retry:
            message += ' (即将重试)'
        
        return self.update_stage_progress(
            task_id=task_id,
            stage=stage,
            progress=0,
            message=message,
            state='failed'
        )
    
    def increment_retry_count(self, task_id: str, stage: str) -> int:
        """增加重试次数"""
        steps_key = self._get_steps_key(task_id)
        retry_key = f'{stage}_retries'
        
        current = self.redis.hget(steps_key, retry_key) or '0'
        new_count = int(current) + 1
        
        self.redis.hset(steps_key, retry_key, str(new_count))
        
        return new_count
    
    def _calculate_overall_progress(self, task_id: str) -> int:
        """计算总体进度 (加权平均)"""
        steps_key = self._get_steps_key(task_id)
        
        total = 0
        for stage, weight in self.stage_weights.items():
            progress_str = self.redis.hget(steps_key, f'{stage}_progress')
            if progress_str:
                progress = int(progress_str)
                total += progress * weight / 100
        
        return int(total)
    
    def _publish_update(self, task_id: str, data: Dict):
        """发布更新到 Pub/Sub"""
        channel = self._get_channel(task_id)
        try:
            self.redis.publish(channel, json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"[ProgressManager] 发布更新失败: {e}")
    
    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """获取任务完整进度数据"""
        progress_key = self._get_progress_key(task_id)
        steps_key = self._get_steps_key(task_id)
        
        progress = self.redis.hgetall(progress_key)
        steps = self.redis.hgetall(steps_key)
        
        if not progress:
            return None
        
        # 解析步骤数据
        stage_data = {}
        for stage in self.stage_weights.keys():
            stage_data[stage] = {
                'status': steps.get(f'{stage}_status', 'pending'),
                'progress': int(steps.get(f'{stage}_progress', 0)),
                'message': steps.get(f'{stage}_message', ''),
                'started_at': steps.get(f'{stage}_started_at', ''),
                'completed_at': steps.get(f'{stage}_completed_at', ''),
                'retries': int(steps.get(f'{stage}_retries', 0)),
            }
        
        return {
            'task_id': progress.get('task_id'),
            'document_url': progress.get('document_url'),
            'status': progress.get('status', 'unknown'),
            'current_stage': progress.get('current_stage'),
            'overall_progress': int(progress.get('overall_progress', 0)),
            'created_at': progress.get('created_at'),
            'updated_at': progress.get('updated_at'),
            'stages': stage_data
        }
    
    def get_task_status(self, task_id: str) -> str:
        """获取任务状态"""
        progress_key = self._get_progress_key(task_id)
        status = self.redis.hget(progress_key, 'status')
        return status or 'unknown'
    
    def complete_task(self, task_id: str, result: Optional[Dict] = None):
        """标记任务完成"""
        progress_key = self._get_progress_key(task_id)
        
        now = datetime.now().isoformat()
        
        self.redis.hset(progress_key, mapping={
            'status': 'completed',
            'overall_progress': '100',
            'completed_at': now,
            'updated_at': now,
            'result': json.dumps(result) if result else '{}'
        })
        
        self._publish_update(task_id, {
            'type': 'completed',
            'task_id': task_id,
            'status': 'completed',
            'overall_progress': 100,
            'message': '所有步骤完成',
            'result': result or {},
            'timestamp': now
        })
    
    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        progress_key = self._get_progress_key(task_id)
        
        now = datetime.now().isoformat()
        
        self.redis.hset(progress_key, mapping={
            'status': 'failed',
            'error': error,
            'failed_at': now,
            'updated_at': now
        })
        
        self._publish_update(task_id, {
            'type': 'failed',
            'task_id': task_id,
            'status': 'failed',
            'message': error,
            'timestamp': now
        })
    
    def cleanup_task(self, task_id: str):
        """清理任务数据"""
        progress_key = self._get_progress_key(task_id)
        steps_key = self._get_steps_key(task_id)
        
        self.redis.delete(progress_key)
        self.redis.delete(steps_key)


# 全局实例
def get_progress_manager() -> ProgressManager:
    """获取 ProgressManager 实例"""
    return ProgressManager()
