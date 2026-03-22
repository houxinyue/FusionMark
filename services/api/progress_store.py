"""
Redis 进度存储类 - 轻量化任务状态管理

替代内存中的 TaskManager，使用 Redis 持久化存储任务状态，
支持 WebSocket 实时推送进度更新。

依赖:
    pip install redis

启动 Redis:
    redis-server
"""

import json
import redis
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path


class RedisProgressStore:
    """
    Redis 进度看板 - 任务状态持久化存储
    
    存储结构:
        Hash: fusionmark:task:status:{task_id} - 任务状态
        PubSub: fusionmark:task:pubsub:{task_id} - 实时进度推送
    """
    
    KEY_PREFIX = "fusionmark:task"
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None,
        username: str = None
    ):
        """
        初始化 Redis 连接
        
        Args:
            host: Redis 主机地址，默认从环境变量 REDIS_HOST 读取，否则 localhost
            port: Redis 端口，默认从环境变量 REDIS_PORT 读取，否则 6379
            db: Redis 数据库，默认从环境变量 REDIS_DB 读取，否则 0
            password: Redis 密码，默认从环境变量 REDIS_PASSWORD 读取
            username: Redis 用户名，默认从环境变量 REDIS_USERNAME 读取
        """
        import os
        
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DATABASE", "0"))
        self.password = password or os.getenv("REDIS_PASSWORD") or None
        self.username = username or os.getenv("REDIS_USERNAME") or None
        
        # 使用 redis.Redis 构造函数
        connection_kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "decode_responses": True
        }
        
        # 只有设置了密码才添加认证参数
        if self.password:
            connection_kwargs["password"] = self.password
        if self.username:
            connection_kwargs["username"] = self.username
        
        self.redis = redis.Redis(**connection_kwargs)
    
    def _status_key(self, task_id: str) -> str:
        """生成任务状态 Hash 的 key"""
        return f"{self.KEY_PREFIX}:status:{task_id}"
    
    def _pubsub_key(self, task_id: str) -> str:
        """生成 PubSub 频道的 key"""
        return f"{self.KEY_PREFIX}:pubsub:{task_id}"
    
    def create_task(self, task_id: str, document_url: str) -> Dict[str, Any]:
        """
        创建新任务，初始化进度
        
        Args:
            task_id: 任务唯一标识
            document_url: 文档 URL
            
        Returns:
            任务初始状态字典
        """
        now = datetime.now().isoformat()
        task_data = {
            "task_id": task_id,
            "document_url": document_url,
            "status": "pending",
            "stage": "pending",
            "stage_progress": "5",
            "overall_progress": "5",
            "message": "任务已接收，准备处理...",
            "created_at": now,
            "updated_at": now,
            "result": "",
            # 各阶段详情（JSON 序列化存储）
            "mineru": json.dumps({
                "state": "pending",
                "progress": 0,
                "current_page": 0,
                "total_pages": 0,
                "logs": []
            }),
            "extraction": json.dumps({
                "state": "pending",
                "progress": 0,
                "extracted_count": 0,
                "logs": []
            }),
            "highlight": json.dumps({
                "state": "pending",
                "progress": 0,
                "highlighted_count": 0,
                "logs": []
            })
        }
        
        key = self._status_key(task_id)
        self.redis.hset(key, mapping=task_data)
        
        # 发布创建事件
        self._publish(task_id, {
            "type": "created",
            "task_id": task_id,
            "status": "pending",
            "progress": 5,
            "stage": "pending",
            "message": "任务已接收，准备处理...",
            "created_at": now
        })
        
        return self._deserialize_task(task_data)
    
    def update_progress(
        self,
        task_id: str,
        stage: str = None,
        stage_progress: int = None,
        overall_progress: int = None,
        message: str = None,
        status: str = None,
        mineru_data: Dict = None,
        extraction_data: Dict = None,
        highlight_data: Dict = None,
        result: Dict = None
    ) -> Dict[str, Any]:
        """
        更新任务进度，同时发布 PubSub 消息
        
        Args:
            task_id: 任务 ID
            stage: 当前阶段 (pending/mineru/extraction/highlight/completed/failed)
            stage_progress: 当前阶段进度 0-100
            overall_progress: 总体进度 0-100
            message: 状态消息
            status: 任务状态 (pending/processing/completed/failed)
            mineru_data: MinerU 阶段详情
            extraction_data: 实体提取阶段详情
            highlight_data: 高亮渲染阶段详情
            result: 任务结果
            
        Returns:
            更新后的任务状态字典
        """
        key = self._status_key(task_id)
        
        # 构建更新数据
        update_data = {"updated_at": datetime.now().isoformat()}
        
        if stage is not None:
            update_data["stage"] = stage
        if stage_progress is not None:
            update_data["stage_progress"] = str(stage_progress)
        if overall_progress is not None:
            update_data["overall_progress"] = str(overall_progress)
        if message is not None:
            update_data["message"] = message
        if status is not None:
            update_data["status"] = status
        if result is not None:
            update_data["result"] = json.dumps(result) if isinstance(result, dict) else str(result)
        
        # 更新阶段详情
        if mineru_data is not None:
            update_data["mineru"] = json.dumps(mineru_data)
        if extraction_data is not None:
            update_data["extraction"] = json.dumps(extraction_data)
        if highlight_data is not None:
            update_data["highlight"] = json.dumps(highlight_data)
        
        # 更新 Redis Hash
        self.redis.hset(key, mapping=update_data)
        
        # 获取完整状态用于发布
        full_task = self.get_task(task_id)
        
        # 发布实时通知
        self._publish(task_id, {
            "type": "progress",
            **{k: v for k, v in full_task.items() if k != "result"}
        })
        
        return full_task
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务完整状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务状态字典，不存在返回 None
        """
        key = self._status_key(task_id)
        data = self.redis.hgetall(key)
        
        if not data:
            return None
        
        return self._deserialize_task(data)
    
    def list_tasks(self, limit: int = 100) -> list:
        """
        列出所有任务（扫描所有任务，生产环境建议使用索引）
        
        Args:
            limit: 最大返回数量
            
        Returns:
            任务列表
        """
        pattern = f"{self.KEY_PREFIX}:status:*"
        tasks = []
        
        for key in self.redis.scan_iter(match=pattern, count=limit):
            task_id = key.split(":")[-1]
            task = self.get_task(task_id)
            if task:
                tasks.append(task)
        
        # 按创建时间倒序
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return tasks[:limit]
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务记录
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否成功删除
        """
        key = self._status_key(task_id)
        return self.redis.delete(key) > 0
    
    def _publish(self, task_id: str, data: Dict[str, Any]):
        """发布进度更新到 PubSub"""
        channel = self._pubsub_key(task_id)
        self.redis.publish(channel, json.dumps(data))
    
    def _deserialize_task(self, data: Dict[str, str]) -> Dict[str, Any]:
        """将 Redis Hash 数据反序列化为任务字典"""
        task = dict(data)
        
        # 反序列化 JSON 字段
        for field in ["mineru", "extraction", "highlight", "result"]:
            if field in task and task[field]:
                try:
                    task[field] = json.loads(task[field])
                except json.JSONDecodeError:
                    pass  # 保持原字符串
        
        # 转换数字字段
        for field in ["stage_progress", "overall_progress"]:
            if field in task:
                try:
                    task[field] = int(task[field])
                except (ValueError, TypeError):
                    task[field] = 0
        
        return task
    
    def get_pubsub_channel(self, task_id: str) -> str:
        """获取 PubSub 频道名称（供 WebSocket 订阅）"""
        return self._pubsub_key(task_id)
    
    def ping(self) -> bool:
        """检查 Redis 连接是否正常"""
        try:
            return self.redis.ping()
        except Exception:
            return False


# 全局实例（单例模式）
_progress_store: Optional[RedisProgressStore] = None


def get_progress_store(
    host: str = None,
    port: int = None,
    db: int = None,
    password: str = None,
    username: str = None
) -> RedisProgressStore:
    """
    获取全局 RedisProgressStore 实例
    
    Args:
        host: Redis 主机地址
        port: Redis 端口
        db: Redis 数据库
        password: Redis 密码
        username: Redis 用户名
        
    Returns:
        RedisProgressStore 实例
    """
    global _progress_store
    if _progress_store is None:
        _progress_store = RedisProgressStore(
            host=host,
            port=port,
            db=db,
            password=password,
            username=username
        )
    return _progress_store


def reset_progress_store():
    """重置全局实例（用于测试）"""
    global _progress_store
    _progress_store = None
