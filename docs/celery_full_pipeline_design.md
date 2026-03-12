# 全异步工作流架构设计

## 愿景

将完整流程 **MinerU → LangExtract → 高亮渲染** 全部纳入 Celery 异步体系，实现：
- ✅ 全链路进度实时追踪
- ✅ 单步骤失败重试（不用从头开始）
- ✅ 支持并发处理多个文档
- ✅ 水平扩展 Worker 节点

---

## 新架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户前端                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  文件上传    │  │  URL输入     │  │  WebSocket进度监听   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          └─────────────────┼─────────────────────┘
                            │ POST /api/v1/tasks
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI API 层                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. 接收请求 → 创建任务记录 → 提交 Celery Chain          │  │
│  │  2. WebSocket 监听 Redis 进度 → 推送到前端                │  │
│  │  3. 状态查询 / 结果下载                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ 提交 Celery Chain
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Celery 任务编排层                            │
│                                                                 │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │  MinerU     │ ──▶ │ LangExtract │ ──▶ │  Highlight  │      │
│   │  解析任务   │     │  提取任务   │     │  渲染任务   │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│          │                   │                   │              │
│          ▼                   ▼                   ▼              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │ 进度: 0-40% │     │ 进度: 40-70%│     │ 进度: 70-100│      │
│   │ 回调更新    │     │ 状态更新    │     │ 分步更新    │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                 │
│   失败处理:                                                     │
│   - 单个步骤失败 → 该步骤重试 (max_retries=3)                  │
│   - 重试耗尽 → 标记任务失败 → 通知前端                          │
└─────────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ MinerU API │  │ LLM API    │  │ PDF渲染    │
    │  (外部)    │  │ (外部)     │  │ (本地)     │
    └────────────┘  └────────────┘  └────────────┘
```

---

## 核心改进点

### 1. 每个步骤独立 Celery 任务

```python
# celery_tasks.py

from celery import chain, shared_task
from celery.exceptions import SoftTimeLimitExceeded

@shared_task(bind=True, max_retries=3, soft_time_limit=600)
def step1_mineru_parse(self, task_id: str, url: str, config: dict):
    """
    步骤1: MinerU 文档解析
    
    特性:
    - 支持进度回调 (轮询 MinerU API)
    - 失败可重试
    - 超时保护 (10分钟)
    """
    try:
        update_progress(task_id, 'mineru', 0, '开始解析...')
        
        # MinerU 有进度回调
        def mineru_callback(attempt, state, data):
            progress = calculate_progress(state, data)
            update_progress(task_id, 'mineru', progress, f'解析中... ({state})')
            # 实时推送 WebSocket
            publish_ws_message(task_id, 'mineru', progress)
        
        result = mineru_client.process_document(
            url=url,
            wait_callback=mineru_callback
        )
        
        update_progress(task_id, 'mineru', 100, '解析完成')
        
        # 返回结果给下一步
        return {
            'status': 'success',
            'md_content': result.md_content,
            'mineru_task_id': result.task_id,
            'total_pages': result.total_pages
        }
        
    except SoftTimeLimitExceeded:
        self.retry(countdown=60)
    except Exception as exc:
        # 记录失败原因
        update_progress(task_id, 'mineru', 0, f'解析失败: {str(exc)}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def step2_langextract(self, task_id: str, step1_result: dict, config: dict):
    """
    步骤2: LangExtract 实体提取
    
    特性:
    - 虽然是阻塞调用，但有状态更新
    - 支持步骤重试 (LangExtract 偶发超时)
    """
    try:
        # 进入阶段
        update_progress(task_id, 'extraction', 10, '准备提取配置...')
        publish_ws_message(task_id, 'extraction', 10)
        
        time.sleep(0.5)  # 让前端看到进度
        
        # 调用大模型前
        update_progress(task_id, 'extraction', 20, '调用大模型分析（约需1-3分钟）...')
        publish_ws_message(task_id, 'extraction', 20)
        
        # LangExtract 阻塞调用 (2-3分钟)
        # 这里会卡住，但前端已经看到"调用大模型中"的状态
        result = langextract.extract(
            text_or_documents=step1_result['md_content'],
            prompt_description=config['prompt'],
            examples=config['examples'],
            model_id=config['model_id']
        )
        
        # 返回结果
        extraction_count = len(result.extractions)
        
        update_progress(task_id, 'extraction', 100, f'提取完成，共{extraction_count}个实体')
        publish_ws_message(task_id, 'extraction', 100)
        
        return {
            'status': 'success',
            'extraction_count': extraction_count,
            'extractions': result.extractions,
            'highlight_count': len(result.highlights)
        }
        
    except SoftTimeLimitExceeded:
        # LangExtract 超时，可能是模型响应慢
        update_progress(task_id, 'extraction', 0, '提取超时，准备重试...')
        self.retry(countdown=30)
    except Exception as exc:
        update_progress(task_id, 'extraction', 0, f'提取失败: {str(exc)}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2, soft_time_limit=120)
def step3_highlight_render(self, task_id: str, step2_result: dict, config: dict):
    """
    步骤3: 高亮渲染
    
    特性:
    - 分步更新进度 (PDF生成、字体加载等)
    - 本地计算，通常很快
    """
    try:
        update_progress(task_id, 'highlight', 0, '开始渲染PDF...')
        publish_ws_message(task_id, 'highlight', 0)
        
        # 准备阶段
        update_progress(task_id, 'highlight', 20, '准备渲染数据...')
        
        # 渲染阶段
        update_progress(task_id, 'highlight', 50, '生成高亮HTML...')
        
        # PDF生成
        update_progress(task_id, 'highlight', 80, '渲染PDF...')
        
        result = md_highlight_service.render(
            md_content=step2_result['md_content'],
            extractions=step2_result['extractions'],
            output_path=config['output_path']
        )
        
        update_progress(task_id, 'highlight', 100, '渲染完成')
        publish_ws_message(task_id, 'highlight', 100)
        
        return {
            'status': 'success',
            'output_path': result.output_path,
            'highlight_count': result.highlight_count
        }
        
    except Exception as exc:
        update_progress(task_id, 'highlight', 0, f'渲染失败: {str(exc)}')
        raise self.retry(exc=exc, countdown=30)


@shared_task
def on_pipeline_success(task_id: str, results: list):
    """整个流程完成后的回调"""
    final_result = {
        'mineru': results[0],
        'extraction': results[1],
        'highlight': results[2]
    }
    
    update_task_status(task_id, 'completed', '处理完成', final_result)
    publish_ws_message(task_id, 'completed', 100, '所有步骤完成')


@shared_task
def on_pipeline_failure(task_id: str, exc: Exception):
    """流程失败处理"""
    update_task_status(task_id, 'failed', f'处理失败: {str(exc)}')
    publish_ws_message(task_id, 'failed', 0, str(exc))
```

---

### 2. Celery Chain 编排

```python
# api_server.py

from celery import chain
from celery_tasks import (
    step1_mineru_parse, 
    step2_langextract, 
    step3_highlight_render,
    on_pipeline_success,
    on_pipeline_failure
)

@app.post("/api/v1/tasks")
async def submit_task(request: SubmitTaskRequest):
    """提交异步任务链"""
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task_manager.create_task(task_id, str(request.document_url))
    
    # 构建 Celery Chain
    # step1 → step2 → step3
    pipeline = chain(
        step1_mineru_parse.s(task_id, str(request.document_url), request.dict()),
        step2_langextract.s(task_id, request.dict()),
        step3_highlight_render.s(task_id, request.dict())
    )
    
    # 提交任务链
    result = pipeline.apply_async(
        link=on_pipeline_success.s(task_id),      # 成功回调
        link_error=on_pipeline_failure.s(task_id)  # 失败回调
    )
    
    # 保存 chain 的 root task id
    task_manager.update_task(
        task_id,
        celery_chain_id=result.id,
        status='processing'
    )
    
    return TaskResponse(
        task_id=task_id,
        status="processing",
        message="任务已提交，正在处理中"
    )
```

---

### 3. 进度聚合与 WebSocket 推送

```python
# progress_manager.py

import redis
import json
from typing import Dict, Any

class ProgressManager:
    """统一进度管理器"""
    
    def __init__(self):
        self.redis = redis.Redis()
        
    def update_progress(self, task_id: str, stage: str, progress: int, message: str):
        """更新进度到 Redis"""
        
        # 1. 存储详细进度
        key = f"task:{task_id}:progress"
        data = {
            'stage': stage,
            'stage_progress': progress,
            'message': message,
            'timestamp': time.time()
        }
        self.redis.hset(key, mapping=data)
        
        # 2. 计算总体进度
        overall = self.calculate_overall_progress(task_id)
        self.redis.hset(key, 'overall_progress', overall)
        
        # 3. 发布到 Pub/Sub (WebSocket 监听)
        channel = f"task:{task_id}:updates"
        self.redis.publish(channel, json.dumps({
            'type': 'progress',
            'stage': stage,
            'progress': progress,
            'overall': overall,
            'message': message
        }))
        
    def calculate_overall_progress(self, task_id: str) -> int:
        """计算总体进度"""
        stage_weights = {
            'mineru': 40,
            'extraction': 30,
            'highlight': 30
        }
        
        total = 0
        for stage, weight in stage_weights.items():
            progress = self.redis.hget(f"task:{task_id}:progress", f"{stage}_progress")
            if progress:
                total += int(progress) * weight / 100
        
        return int(total)
        
    def get_step_status(self, task_id: str) -> Dict[str, Any]:
        """获取各步骤状态"""
        return {
            'mineru': {
                'status': self.redis.hget(f"task:{task_id}:steps", 'mineru_status'),
                'progress': self.redis.hget(f"task:{task_id}:steps", 'mineru_progress'),
                'retries': self.redis.hget(f"task:{task_id}:steps", 'mineru_retries') or 0
            },
            'extraction': {...},
            'highlight': {...}
        }
```

---

### 4. WebSocket 实时推送

```python
# websocket_handler.py

import asyncio
import json
import redis.asyncio as aioredis
from fastapi import WebSocket

class WebSocketProgressHandler:
    """WebSocket 进度处理器"""
    
    def __init__(self):
        self.redis = aioredis.Redis()
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, task_id: str, websocket: WebSocket):
        """建立 WebSocket 连接"""
        await websocket.accept()
        self.active_connections[task_id] = websocket
        
        # 启动 Redis 订阅监听
        asyncio.create_task(self._listen_redis(task_id))
        
    async def _listen_redis(self, task_id: str):
        """监听 Redis Pub/Sub"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"task:{task_id}:updates")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                
                # 推送到前端
                if task_id in self.active_connections:
                    ws = self.active_connections[task_id]
                    await ws.send_json({
                        'type': 'progress',
                        'data': data
                    })
                    
                # 如果完成或失败，关闭连接
                if data.get('stage') in ['completed', 'failed']:
                    await pubsub.unsubscribe()
                    break
                    
    async def disconnect(self, task_id: str):
        """断开连接"""
        if task_id in self.active_connections:
            del self.active_connections[task_id]
```

---

## 前端适配

```javascript
// 新的进度处理逻辑
class PipelineProgress {
    constructor(taskId) {
        this.taskId = taskId;
        this.ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);
        this.stepProgress = {
            mineru: 0,
            extraction: 0,
            highlight: 0
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleProgress(data);
        };
    }
    
    handleProgress(data) {
        const { stage, progress, overall, message } = data.data;
        
        // 更新各步骤进度
        if (stage in this.stepProgress) {
            this.stepProgress[stage] = progress;
            this.updateStepUI(stage, progress, message);
        }
        
        // 更新总体进度
        this.updateOverallProgress(overall, message);
        
        // 检查完成
        if (stage === 'completed') {
            this.onComplete();
        } else if (stage === 'failed') {
            this.onFailed(message);
        }
    }
    
    updateStepUI(stage, progress, message) {
        // 更新步骤状态
        const stepEl = document.querySelector(`[data-step="${stage}"]`);
        if (stepEl) {
            stepEl.classList.add('active');
            const label = stepEl.querySelector('.step-label');
            label.textContent = `${this.getStepName(stage)} (${progress}%)`;
        }
        
        // 更新进度条
        document.getElementById('progressFill').style.width = `${progress}%`;
        document.getElementById('progressStatus').textContent = message;
    }
}
```

---

## 部署架构

```
                    ┌─────────────────┐
                    │   Nginx (负载)   │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ FastAPI-1   │   │ FastAPI-2   │   │ FastAPI-3   │
    │ (Web/API)   │   │ (Web/API)   │   │ (Web/API)   │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                    ┌────────┴────────┐
                    │    Redis        │
                    │  (Broker + DB)  │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ Worker-1    │   │ Worker-2    │   │ Worker-3    │
    │ (MinerU)    │   │ (LangExtract)│   │ (Highlight) │
    └─────────────┘   └─────────────┘   └─────────────┘
```

---

## 实施路线图

### Phase 1: 基础改造 (2天)
- [ ] 重构 `celery_config.py`，支持 Redis Broker
- [ ] 创建 `progress_manager.py` 统一进度管理
- [ ] 更新 `celery_tasks.py`，实现 3 个步骤任务
- [ ] 更新 `api_server.py`，使用 Chain 提交任务

### Phase 2: WebSocket 适配 (1天)
- [ ] 实现 `WebSocketProgressHandler`
- [ ] 前端适配新的进度数据结构
- [ ] 步骤状态独立显示

### Phase 3: 测试优化 (2天)
- [ ] 单步骤失败重试测试
- [ ] 并发处理测试
- [ ] 进度推送延迟优化
- [ ] 部署文档编写

---

## 与当前架构对比

| 特性 | 当前架构 | 新架构 (Celery Chain) |
|------|----------|----------------------|
| MinerU 进度 | ✅ 实时回调 | ✅ 实时 + 可重试 |
| LangExtract 进度 | ❌ 卡死3分钟 | ✅ 状态更新 + 可重试 |
| 高亮渲染进度 | ⚠️ 模拟进度 | ✅ 真实分步进度 |
| 单步骤失败 | ❌ 全部重来 | ✅ 仅重试该步骤 |
| 并发处理 | ❌ 阻塞 | ✅ Worker 并发 |
| 水平扩展 | ❌ 单机 | ✅ 多 Worker 节点 |

---

## 总结

新架构将**每个处理步骤都独立为 Celery 任务**，通过 Chain 串联，实现了：

1. **全链路可观测** - 每个步骤独立进度、状态
2. **单步骤可重试** - MinerU/LangExtract/渲染 任一步骤失败都可单独重试
3. **高并发支持** - 多个 Worker 并行处理多个文档
4. **更好的用户体验** - LangExtract 期间也有状态反馈

---

**文档版本**: 2.0  
**创建日期**: 2026-03-03  
**关联任务**: fusion-mark-csy
