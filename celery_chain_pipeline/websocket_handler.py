"""
WebSocket 进度处理器

负责监听 Redis Pub/Sub 并将进度实时推送到前端 WebSocket

使用方式:
    @app.websocket("/ws/{task_id}")
    async def websocket_endpoint(websocket: WebSocket, task_id: str):
        handler = WebSocketProgressHandler()
        await handler.connect(task_id, websocket)
        try:
            await handler.listen(task_id)
        except WebSocketDisconnect:
            await handler.disconnect(task_id)
"""

import json
import asyncio
import redis.asyncio as aioredis
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketProgressHandler:
    """WebSocket 进度处理器"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化 WebSocket 进度处理器
        
        Args:
            redis_url: Redis 连接地址，默认从环境变量读取
        """
        import os
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.websocket: Optional[WebSocket] = None
        self.task_id: Optional[str] = None
        self._running = False
    
    async def connect(self, task_id: str, websocket: WebSocket):
        """
        建立 WebSocket 连接
        
        Args:
            task_id: 任务 ID
            websocket: FastAPI WebSocket 对象
        """
        self.task_id = task_id
        self.websocket = websocket
        
        # 接受 WebSocket 连接
        await websocket.accept()
        
        # 初始化异步 Redis 连接
        self.redis = await aioredis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_connect_timeout=30,
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # 发送连接成功消息
        await self._send_message({
            "type": "connected",
            "task_id": task_id,
            "message": "WebSocket 连接成功"
        })
        
        # 立即发送当前进度
        await self._send_current_progress()
    
    async def _send_current_progress(self):
        """发送当前进度数据"""
        if not self.redis or not self.task_id:
            return
        
        try:
            # 从 Redis 获取当前进度
            progress_key = f"task:{self.task_id}:progress"
            steps_key = f"task:{self.task_id}:steps"
            
            progress = await self.redis.hgetall(progress_key)
            steps = await self.redis.hgetall(steps_key)
            
            if progress:
                # 构建阶段数据
                stage_weights = {
                    'mineru': 40,
                    'extraction': 30,
                    'highlight': 30
                }
                stage_names = {
                    'mineru': '文档解析',
                    'extraction': '实体提取',
                    'highlight': '高亮渲染'
                }
                
                stage_data = {}
                for stage in stage_weights.keys():
                    stage_data[stage] = {
                        'status': steps.get(f'{stage}_status', 'pending'),
                        'progress': int(steps.get(f'{stage}_progress', 0)),
                        'message': steps.get(f'{stage}_message', ''),
                        'started_at': steps.get(f'{stage}_started_at', ''),
                        'completed_at': steps.get(f'{stage}_completed_at', ''),
                        'retries': int(steps.get(f'{stage}_retries', 0)),
                        'name': stage_names.get(stage, stage)
                    }
                
                await self._send_message({
                    "type": "progress",
                    "task_id": self.task_id,
                    "status": progress.get('status', 'unknown'),
                    "current_stage": progress.get('current_stage'),
                    "overall_progress": int(progress.get('overall_progress', 0)),
                    "stages": stage_data,
                    "message": "当前进度"
                })
            else:
                # 任务不存在
                await self._send_message({
                    "type": "error",
                    "task_id": self.task_id,
                    "message": "任务不存在或已过期"
                })
                
        except Exception as e:
            await self._send_message({
                "type": "error",
                "message": f"获取进度失败: {str(e)}"
            })
    
    async def listen(self, task_id: str):
        """
        监听 Redis Pub/Sub 并推送消息
        
        Args:
            task_id: 任务 ID
        """
        self._running = True
        channel = f"task:{task_id}:updates"
        
        try:
            # 创建 Pub/Sub 订阅
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(channel)
            
            # 监听消息
            async for message in self.pubsub.listen():
                if not self._running:
                    break
                
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        
                        # 推送到 WebSocket
                        await self._send_message(data)
                        
                        # 如果任务完成或失败，停止监听
                        if data.get('type') in ('completed', 'failed'):
                            # 等待一小段时间确保消息发送完成
                            await asyncio.sleep(0.5)
                            break
                            
                    except json.JSONDecodeError:
                        # 忽略非 JSON 消息
                        pass
                    except Exception as e:
                        print(f"[WebSocketHandler] 处理消息失败: {e}")
                        
        except asyncio.CancelledError:
            # 任务被取消
            pass
        except Exception as e:
            print(f"[WebSocketHandler] 监听异常: {e}")
            await self._send_message({
                "type": "error",
                "message": f"监听异常: {str(e)}"
            })
        finally:
            await self._cleanup()
    
    async def _send_message(self, data: Dict):
        """发送消息到 WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send_json(data)
            except Exception as e:
                print(f"[WebSocketHandler] 发送消息失败: {e}")
    
    async def disconnect(self, task_id: str):
        """断开连接"""
        self._running = False
        await self._cleanup()
    
    async def _cleanup(self):
        """清理资源"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
                self.pubsub = None
        except Exception:
            pass
        
        try:
            if self.redis:
                await self.redis.close()
                self.redis = None
        except Exception:
            pass
        
        self.websocket = None
        self._running = False
    
    async def handle_client_messages(self, task_id: str):
        """
        处理客户端发来的消息 (如心跳、查询请求)
        
        在独立的 task 中运行，与 listen 并行
        """
        try:
            while self._running:
                try:
                    # 接收客户端消息
                    data = await self.websocket.receive_json()
                    
                    msg_type = data.get('type')
                    
                    if msg_type == 'ping':
                        # 心跳响应
                        await self._send_message({
                            "type": "pong",
                            "timestamp": data.get('timestamp')
                        })
                    
                    elif msg_type == 'get_progress':
                        # 主动查询进度
                        await self._send_current_progress()
                    
                    elif msg_type == 'close':
                        # 客户端请求关闭
                        break
                        
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    print(f"[WebSocketHandler] 处理客户端消息失败: {e}")
                    
        except asyncio.CancelledError:
            pass


# 便捷函数
async def handle_websocket(websocket: WebSocket, task_id: str, redis_url: Optional[str] = None):
    """
    处理 WebSocket 连接的便捷函数
    
    使用方式:
        @app.websocket("/ws/{task_id}")
        async def websocket_endpoint(websocket: WebSocket, task_id: str):
            await handle_websocket(websocket, task_id)
    """
    handler = WebSocketProgressHandler(redis_url)
    await handler.connect(task_id, websocket)
    
    try:
        # 同时运行监听和客户端消息处理
        listen_task = asyncio.create_task(handler.listen(task_id))
        client_task = asyncio.create_task(handler.handle_client_messages(task_id))
        
        # 等待任意一个任务完成
        done, pending = await asyncio.wait(
            [listen_task, client_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 取消其他任务
        for task in pending:
            task.cancel()
            
    except WebSocketDisconnect:
        pass
    finally:
        await handler.disconnect(task_id)
