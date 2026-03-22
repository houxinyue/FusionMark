"""
WebSocket 进度推送处理器 - Redis PubSub 集成

使用 Redis PubSub 实现多客户端实时进度同步，
替代原有的内存回调机制。

依赖:
    pip install redis websockets
"""

import json
import asyncio
import redis
from typing import Dict, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketProgressHandler:
    """
    WebSocket 进度推送处理器
    
    功能:
    1. 管理 WebSocket 连接
    2. 订阅 Redis PubSub 接收进度更新
    3. 向客户端推送实时进度
    
    架构:
        Client1 ──┐
        Client2 ──┼──► WebSocket Handler ──► Redis PubSub (订阅)
        Client3 ──┘                              ▲
                                               │
        Background Task ─────────────────────────┘ (发布)
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None,
        username: str = None
    ):
        """
        初始化处理器
        
        Args:
            host: Redis 主机地址
            port: Redis 端口
            db: Redis 数据库
            password: Redis 密码
            username: Redis 用户名
        """
        import os
        
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DATABASE", "0"))
        self.password = password or os.getenv("REDIS_PASSWORD") or None
        self.username = username or os.getenv("REDIS_USERNAME") or None
        
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        
        # 任务 -> WebSocket 集合的映射
        self._connections: Dict[str, Set[WebSocket]] = {}
        # 任务 -> PubSub 订阅线程的映射
        self._subscriptions: Dict[str, asyncio.Task] = {}
    
    async def handle(self, websocket: WebSocket, task_id: str, progress_store):
        """
        处理 WebSocket 连接
        
        Args:
            websocket: FastAPI WebSocket 对象
            task_id: 任务 ID
            progress_store: RedisProgressStore 实例
        """
        await websocket.accept()
        
        # 1. 获取当前任务状态
        task_data = progress_store.get_task(task_id)
        
        if not task_data:
            await websocket.send_json({
                "type": "connected",
                "data": {"error": "任务不存在"}
            })
            await websocket.close(code=4004, reason="Task not found")
            return
        
        # 2. 发送初始状态
        await websocket.send_json({
            "type": "connected",
            "data": task_data
        })
        
        # 3. 注册连接
        self._register_connection(task_id, websocket)
        
        # 4. 启动 PubSub 订阅（如果尚未订阅）
        if task_id not in self._subscriptions:
            self._start_pubsub_subscription(task_id, progress_store)
        
        try:
            # 5. 保持连接，接收客户端消息
            while True:
                try:
                    # 设置接收超时，用于定期发送心跳
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=30.0
                    )
                    
                    # 处理客户端消息
                    if data == "ping":
                        await websocket.send_text("pong")
                    elif data == "close":
                        break
                    else:
                        # 尝试解析 JSON 消息
                        try:
                            msg = json.loads(data)
                            await self._handle_client_message(websocket, task_id, msg)
                        except json.JSONDecodeError:
                            pass
                            
                except asyncio.TimeoutError:
                    # 发送服务端心跳
                    await websocket.send_json({"type": "heartbeat"})
                    
        except WebSocketDisconnect:
            print(f"[WebSocket] 客户端断开: {task_id}")
        except Exception as e:
            print(f"[WebSocket] 错误: {task_id} - {e}")
        finally:
            # 6. 清理连接
            self._unregister_connection(task_id, websocket)
    
    def _register_connection(self, task_id: str, websocket: WebSocket):
        """注册 WebSocket 连接"""
        if task_id not in self._connections:
            self._connections[task_id] = set()
        self._connections[task_id].add(websocket)
        print(f"[WebSocket] 连接注册: {task_id} (当前 {len(self._connections[task_id])} 个连接)")
    
    def _unregister_connection(self, task_id: str, websocket: WebSocket):
        """注销 WebSocket 连接"""
        if task_id in self._connections:
            self._connections[task_id].discard(websocket)
            
            # 如果没有连接了，取消订阅
            if not self._connections[task_id]:
                del self._connections[task_id]
                self._stop_pubsub_subscription(task_id)
                print(f"[WebSocket] 取消订阅: {task_id} (无连接)")
            else:
                print(f"[WebSocket] 连接注销: {task_id} (剩余 {len(self._connections[task_id])} 个连接)")
    
    def _start_pubsub_subscription(self, task_id: str, progress_store):
        """启动 PubSub 订阅任务"""
        channel = progress_store.get_pubsub_channel(task_id)
        
        # 创建订阅任务
        task = asyncio.create_task(
            self._pubsub_listener(task_id, channel),
            name=f"pubsub-{task_id}"
        )
        self._subscriptions[task_id] = task
        print(f"[PubSub] 开始订阅: {channel}")
    
    def _stop_pubsub_subscription(self, task_id: str):
        """停止 PubSub 订阅"""
        if task_id in self._subscriptions:
            task = self._subscriptions[task_id]
            task.cancel()
            del self._subscriptions[task_id]
    
    async def _pubsub_listener(self, task_id: str, channel: str):
        """
        PubSub 订阅监听循环
        
        在单独的异步任务中运行，接收 Redis 发布的消息并推送给所有连接的客户端。
        """
        # 创建独立的 Redis 连接用于 PubSub
        import redis.asyncio as aioredis
        
        redis_client = None
        pubsub = None
        
        try:
            # 构建连接参数
            connection_kwargs = {
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "decode_responses": True
            }
            if self.password:
                connection_kwargs["password"] = self.password
            if self.username:
                connection_kwargs["username"] = self.username
            
            redis_client = aioredis.Redis(**connection_kwargs)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            print(f"[PubSub] 已订阅频道: {channel}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    
                    # 推送给所有连接的客户端
                    await self._broadcast(task_id, {
                        "type": "progress",
                        "data": data
                    })
                    
                    # 如果任务完成或失败，可选：保持连接一段时间再关闭
                    status = data.get("status")
                    if status in ["completed", "failed"]:
                        # 等待一小段时间确保客户端收到最后消息
                        await asyncio.sleep(1)
                        # 注意：这里不关闭连接，让客户端自己决定何时断开
        
        except asyncio.CancelledError:
            print(f"[PubSub] 订阅取消: {channel}")
        except Exception as e:
            print(f"[PubSub] 订阅错误: {channel} - {e}")
        finally:
            if pubsub:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            if redis_client:
                await redis_client.close()
    
    async def _broadcast(self, task_id: str, message: dict):
        """向任务的所有连接广播消息"""
        if task_id not in self._connections:
            return
        
        disconnected = set()
        
        for websocket in self._connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                disconnected.add(websocket)
        
        # 清理断开的连接
        for ws in disconnected:
            self._connections[task_id].discard(ws)
    
    async def _handle_client_message(self, websocket: WebSocket, task_id: str, message: dict):
        """处理客户端发送的消息"""
        msg_type = message.get("type")
        
        if msg_type == "ping":
            await websocket.send_json({"type": "pong"})
        elif msg_type == "get_status":
            # 客户端请求最新状态
            from .progress_store import get_progress_store
            store = get_progress_store()
            task_data = store.get_task(task_id)
            if task_data:
                await websocket.send_json({
                    "type": "progress",
                    "data": task_data
                })


# 全局处理器实例
_websocket_handler: Optional[WebSocketProgressHandler] = None


def get_websocket_handler(
    host: str = None,
    port: int = None,
    db: int = None,
    password: str = None,
    username: str = None
) -> WebSocketProgressHandler:
    """
    获取全局 WebSocketProgressHandler 实例
    
    Args:
        host: Redis 主机地址
        port: Redis 端口
        db: Redis 数据库
        password: Redis 密码
        username: Redis 用户名
        
    Returns:
        WebSocketProgressHandler 实例
    """
    global _websocket_handler
    if _websocket_handler is None:
        _websocket_handler = WebSocketProgressHandler(
            host=host,
            port=port,
            db=db,
            password=password,
            username=username
        )
    return _websocket_handler


def reset_websocket_handler():
    """重置全局实例（用于测试）"""
    global _websocket_handler
    _websocket_handler = None
