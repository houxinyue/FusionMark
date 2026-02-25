# PDF 智能解析与高亮 API 文档

FastAPI 提供的 RESTful API 服务，支持 PDF 解析、实体提取和高亮渲染。

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn websockets celery redis
```

### 2. 启动服务

```bash
# 方式 1: 使用启动脚本
python start_server.py api

# 方式 2: 直接使用 uvicorn
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问文档

- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## API 接口

### 1. 提交任务

**POST** `/api/v1/tasks`

提交 PDF 处理任务。

#### 请求参数

```json
{
  "pdf_url": "https://example.com/document.pdf",
  "output_filename": "result.pdf",
  "custom_title": "智能分析报告",
  "custom_prompt": "提取报告标题、公司名称...",
  "model": "vlm",
  "enable_ocr": true,
  "enable_formula": true,
  "enable_table": true,
  "language": "ch"
}
```

#### 响应

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "任务已提交，正在处理中",
  "created_at": "2026-02-13T14:30:00"
}
```

### 2. 查询任务状态

**GET** `/api/v1/tasks/{task_id}`

查询任务执行状态和进度。

#### 响应

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": {
    "mineru_state": "running",
    "mineru_progress": 5,
    "mineru_total": 10,
    "extraction_count": 0,
    "highlight_count": 0
  },
  "message": "MinerU 解析中...",
  "result": null
}
```

状态说明:
- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 完成
- `failed`: 失败

### 3. 列出任务

**GET** `/api/v1/tasks?limit=10&offset=0`

列出最近提交的任务。

### 4. 下载结果

**GET** `/api/v1/tasks/{task_id}/download`

下载处理完成的高亮 PDF 文件。

### 5. 获取默认配置

**GET** `/api/v1/config/default`

获取服务的默认配置。

### 6. 更新配置

**POST** `/api/v1/config`

动态更新服务配置。

```json
{
  "config": {
    "mineru_model": "vlm",
    "mineru_enable_ocr": true,
    "highlight_config": {
      "extraction_prompt": "自定义提示词...",
      "category_colors": [...]
    }
  }
}
```

## WebSocket 实时进度

连接 WebSocket 获取实时进度推送。

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{task_id}');

ws.onopen = () => {
  console.log('WebSocket 已连接');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('进度更新:', data);
};

ws.onclose = () => {
  console.log('WebSocket 已断开');
};
```

### 消息格式

```json
{
  "type": "progress",
  "data": {
    "task_id": "...",
    "status": "processing",
    "progress": {
      "mineru_state": "running",
      "mineru_progress": 5
    }
  }
}
```

## 使用示例

### Python 示例

```python
import requests
import time

# API 地址
BASE_URL = "http://localhost:8000"

# 1. 提交任务
response = requests.post(f"{BASE_URL}/api/v1/tasks", json={
    "pdf_url": "https://example.com/report.pdf",
    "custom_title": "市场分析报告"
})
result = response.json()
task_id = result["task_id"]
print(f"任务已提交: {task_id}")

# 2. 轮询查询状态
while True:
    response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
    status = response.json()
    
    print(f"状态: {status['status']}, 进度: {status['progress']}")
    
    if status["status"] in ["completed", "failed"]:
        break
    
    time.sleep(3)

# 3. 下载结果
if status["status"] == "completed":
    response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}/download")
    with open("output.pdf", "wb") as f:
        f.write(response.content)
    print("结果已下载: output.pdf")
```

### cURL 示例

```bash
# 提交任务
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://example.com/document.pdf",
    "output_filename": "result.pdf"
  }'

# 查询状态
curl "http://localhost:8000/api/v1/tasks/{task_id}"

# 下载结果
curl "http://localhost:8000/api/v1/tasks/{task_id}/download" \
  -o output.pdf
```

## Celery 任务队列

对于大文件或批量处理，使用 Celery 任务队列。

### 启动 Worker

```bash
# 方式 1: 使用启动脚本
python start_server.py worker

# 方式 2: 直接启动
celery -A celery_config worker --loglevel=info -Q pdf_processing
```

### 使用 Celery 任务

```python
from celery_tasks import process_pdf

# 提交异步任务
result = process_pdf.delay(
    pdf_url="https://example.com/large.pdf",
    task_id="my_task"
)

# 获取任务 ID
task_id = result.id
print(f"Celery 任务 ID: {task_id}")

# 查询结果（阻塞等待）
result_data = result.get(timeout=1800)
print(result_data)
```

### Flower 监控

```bash
# 启动 Flower
python start_server.py flower

# 访问监控面板
open http://localhost:5555
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `MINERU_API_KEY` | MinerU API 密钥 | ✅ |
| `DS_API_KEY` | DeepSeek API 密钥 | ✅ |
| `DS_API_BASE_URL` | DeepSeek API 地址 | ✅ |
| `REDIS_URL` | Redis 连接地址 | ❌ (Celery 使用) |

### 配置文件

创建 `my_config.yaml`:

```yaml
mineru_model: "vlm"
mineru_enable_ocr: true
highlight_config:
  extraction_prompt: |
    提取以下信息：...
  category_colors:
    - name: "company"
      color: "#2ecc71"
```

使用配置:

```python
from full_pipeline_service import FullPipelineService

service = FullPipelineService.from_config("my_config.yaml")
```

## 性能优化

### 1. 调整 Worker 并发数

```bash
# 根据 CPU 核心数调整
python start_server.py worker -c 8
```

### 2. 使用多个队列

```bash
# 不同优先级使用不同队列
celery -A celery_config worker -Q high_priority,pdf_processing,default
```

### 3. 文件清理

自动清理过期文件（默认保留 7 天）:

```bash
# 手动触发清理
python -c "from celery_tasks import cleanup_old_files; cleanup_old_files.delay(7)"
```

## 常见问题

### 1. WebSocket 连接失败

检查防火墙设置，确保端口 8000 可访问。

### 2. Celery 任务卡住

检查 Redis 连接:
```bash
redis-cli ping
```

### 3. 内存不足

减少 Worker 并发数:
```bash
python start_server.py worker -c 2
```

### 4. 任务超时

调整任务时间限制（celery_config.py）:
```python
task_time_limit = 3600  # 1小时
```
