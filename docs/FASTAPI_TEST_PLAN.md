# FastAPI Web 服务测试计划

## 概述

本测试计划覆盖 FastAPI Web 服务 (`api_server.py`) 的所有功能，确保 PDF 智能解析与高亮 API 的稳定性和可靠性。

**服务信息:**
- 启动命令: `uvicorn api_server:app --reload --host 0.0.0.0 --port 8000`
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 测试任务清单 (同步至 beads)

### 🔴 P1 - 高优先级 (核心功能)

| ID | 测试项 | 状态 | 说明 |
|----|--------|------|------|
| `fusion-mark-qbk` | 基础 API 功能 - 健康检查与根路径 | ⏳ 待测试 | 验证服务启动和基础端点 |
| `fusion-mark-bl3` | 任务提交 API - POST /api/v1/tasks | ⏳ 待测试 | PDF 处理任务提交功能 |
| `fusion-mark-hm7` | 任务状态查询 API - GET /api/v1/tasks/{task_id} | ⏳ 待测试 | 查询任务状态和进度 |
| `fusion-mark-xob` | 结果下载 API - GET /api/v1/tasks/{task_id}/download | ⏳ 待测试 | 下载高亮 PDF 结果 |
| `fusion-mark-bxp` | WebSocket 实时进度推送 - /ws/{task_id} | ⏳ 待测试 | 实时进度通知 |
| `fusion-mark-5d5` | 完整 PDF 处理流程 E2E 测试 | ⏳ 待测试 | 端到端全流程验证 |

### 🟡 P2 - 中优先级 (辅助功能)

| ID | 测试项 | 状态 | 说明 |
|----|--------|------|------|
| `fusion-mark-4tp` | 任务列表 API - GET /api/v1/tasks | ⏳ 待测试 | 分页查询任务列表 |
| `fusion-mark-jmt` | 配置管理 API - GET/POST /api/v1/config | ⏳ 待测试 | 动态配置获取和更新 |
| `fusion-mark-3yc` | 错误处理与边界情况测试 | ⏳ 待测试 | 异常情况处理 |
| `fusion-mark-7fk` | 并发任务处理性能测试 | ⏳ 待测试 | 多任务并发性能 |
| `fusion-mark-rr9` | 编写自动化测试脚本和文档 | ⏳ 待测试 | 测试脚本和文档 |

---

## 详细测试内容

### 1. 基础 API 功能测试 (`fusion-mark-qbk`)

**测试目标:** 验证服务启动后基础端点可用

**测试项:**
- [ ] GET `/` - 根路径返回服务信息
- [ ] GET `/health` - 健康检查返回状态
- [ ] GET `/docs` - Swagger API 文档可访问
- [ ] GET `/redoc` - ReDoc 文档可访问

**预期结果:**
- 所有端点返回 HTTP 200
- 健康检查返回 `{"status": "healthy", ...}`
- 包含正确的任务统计信息

**测试命令:**
```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

---

### 2. 任务提交 API 测试 (`fusion-mark-bl3`)

**测试目标:** 验证 PDF 处理任务提交功能

**测试项:**
- [ ] 使用有效 PDF URL 提交任务
- [ ] 验证请求参数处理 (output_filename, custom_title, custom_prompt)
- [ ] 验证 MinerU 参数 (model, enable_ocr, enable_formula, enable_table, language)
- [ ] 验证响应包含 task_id 和 pending 状态
- [ ] 测试无效 PDF URL 的错误处理

**预期结果:**
- 成功提交返回 200 和 task_id
- 参数正确传递给后台任务
- 无效 URL 返回 422 验证错误

**测试命令:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://example.com/test.pdf",
    "output_filename": "result.pdf",
    "custom_title": "测试报告",
    "model": "vlm",
    "enable_ocr": true,
    "enable_formula": true,
    "enable_table": true,
    "language": "ch"
  }'
```

---

### 3. 任务状态查询 API 测试 (`fusion-mark-hm7`)

**测试目标:** 验证任务状态查询功能

**测试项:**
- [ ] 查询存在的任务状态
- [ ] 验证状态流转: pending -> processing -> completed/failed
- [ ] 验证进度信息 (mineru_state, mineru_progress, extraction_count, highlight_count)
- [ ] 查询不存在的任务返回 404
- [ ] 验证消息和结果字段

**预期结果:**
- 正确返回任务状态和进度
- 状态随处理过程正确更新
- 不存在任务返回 404
- 完成后包含结果数据

**测试命令:**
```bash
curl http://localhost:8000/api/v1/tasks/{task_id}
```

---

### 4. 任务列表 API 测试 (`fusion-mark-4tp`)

**测试目标:** 验证任务列表查询功能

**测试项:**
- [ ] 获取最近任务列表
- [ ] 验证分页参数 (limit, offset)
- [ ] 验证返回字段完整性
- [ ] 验证任务按创建时间倒序排列
- [ ] 空列表处理

**预期结果:**
- 返回任务总数和分页数据
- 支持分页查询
- 字段包含 task_id, status, created_at 等

**测试命令:**
```bash
curl "http://localhost:8000/api/v1/tasks?limit=5&offset=0"
```

---

### 5. 结果下载 API 测试 (`fusion-mark-xob`)

**测试目标:** 验证高亮 PDF 结果下载功能

**测试项:**
- [ ] 成功完成任务后下载结果
- [ ] 验证返回文件为有效 PDF
- [ ] 任务不存在返回 404
- [ ] 任务未完成时下载返回 400
- [ ] 结果文件不存在时的处理

**预期结果:**
- 成功下载返回 PDF 文件
- Content-Type 为 application/pdf
- 错误情况返回相应状态码

**测试命令:**
```bash
curl http://localhost:8000/api/v1/tasks/{task_id}/download -o result.pdf
```

---

### 6. 配置管理 API 测试 (`fusion-mark-jmt`)

**测试目标:** 验证服务配置的获取和动态更新

**测试项:**
- [ ] GET `/api/v1/config/default` - 获取默认配置
- [ ] POST `/api/v1/config` - 更新配置
- [ ] 验证配置更新后生效
- [ ] 验证无效配置返回 400
- [ ] 配置持久化验证

**预期结果:**
- 获取默认配置成功
- 更新配置后服务使用新配置
- 无效配置返回详细错误信息

**测试命令:**
```bash
# 获取配置
curl http://localhost:8000/api/v1/config/default

# 更新配置
curl -X POST http://localhost:8000/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"config": {"mineru_model": "vlm"}}'
```

---

### 7. WebSocket 实时进度测试 (`fusion-mark-bxp`)

**测试目标:** 验证 WebSocket 实时进度推送功能

**测试项:**
- [ ] 建立 WebSocket 连接
- [ ] 接收初始连接消息 (type: connected)
- [ ] 实时接收进度更新 (type: progress)
- [ ] 心跳机制验证 (ping/pong)
- [ ] 任务完成后的消息通知
- [ ] 连接断开处理

**预期结果:**
- 成功建立 WebSocket 连接
- 实时收到进度更新消息
- 心跳保持连接活跃
- 正确断开连接

**测试代码:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{task_id}');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};
ws.onclose = () => console.log('Disconnected');
```

---

### 8. 完整 PDF 处理流程 E2E 测试 (`fusion-mark-5d5`)

**测试目标:** 验证从提交到下载的完整流程

**测试项:**
- [ ] 提交 PDF 处理任务
- [ ] 轮询查询任务状态直到完成
- [ ] 验证任务成功完成
- [ ] 下载高亮 PDF 文件
- [ ] 验证 PDF 文件包含高亮内容

**测试流程:**
1. 提交任务获取 task_id
2. 每隔 3 秒查询状态
3. 等待状态变为 completed 或 failed
4. 下载结果文件
5. 验证文件完整性

**Python 测试脚本:**
```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. 提交任务
response = requests.post(f"{BASE_URL}/api/v1/tasks", json={
    "pdf_url": "https://example.com/report.pdf"
})
task_id = response.json()["task_id"]

# 2. 轮询状态
while True:
    status = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}").json()
    print(f"Status: {status['status']}, Progress: {status['progress']}")
    if status["status"] in ["completed", "failed"]:
        break
    time.sleep(3)

# 3. 下载结果
if status["status"] == "completed":
    response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}/download")
    with open("output.pdf", "wb") as f:
        f.write(response.content)
    print("Downloaded: output.pdf")
```

---

### 9. 错误处理与边界情况测试 (`fusion-mark-3yc`)

**测试目标:** 验证异常情况处理

**测试项:**
- [ ] 无效的 PDF URL 格式
- [ ] 不可访问的 PDF URL
- [ ] 查询不存在的 task_id
- [ ] 下载未完成任务的结果
- [ ] 过大的 PDF 文件处理
- [ ] 特殊字符文件名处理
- [ ] 并发修改同一任务

**预期结果:**
- 返回适当的 HTTP 状态码
- 错误消息清晰明确
- 服务保持稳定不崩溃

---

### 10. 并发任务处理性能测试 (`fusion-mark-7fk`)

**测试目标:** 验证多任务并发处理能力

**测试项:**
- [ ] 同时提交 5 个任务
- [ ] 同时提交 10 个任务
- [ ] 监控任务处理时间
- [ ] 检查内存使用情况
- [ ] 验证任务状态不混乱

**性能指标:**
- 单任务平均处理时间
- 并发任务下的响应时间
- 内存占用峰值
- CPU 使用率

---

### 11. 自动化测试脚本编写 (`fusion-mark-rr9`)

**测试目标:** 创建可重复的自动化测试

**交付物:**
- [ ] `tests/test_api_server.py` - pytest 测试脚本
- [ ] `tests/test_websocket.py` - WebSocket 测试
- [ ] `tests/test_e2e.py` - 端到端测试
- [ ] `tests/conftest.py` - 测试配置和固件
- [ ] 测试数据 (示例 PDF 文件)

---

## 测试环境要求

### 必需服务
- [ ] FastAPI 服务运行 (`api_server.py`)
- [ ] 环境变量配置 (MINERU_API_KEY, DS_API_KEY)
- [ ] Redis (如果使用 Celery)

### 测试数据
- [ ] 有效的 PDF 文件 URL
- [ ] 不同语言的 PDF (中文、英文)
- [ ] 包含表格的 PDF
- [ ] 包含公式的 PDF
- [ ] 扫描版 PDF (OCR 测试)

---

## 测试执行计划

### 阶段 1: 基础功能验证
1. 启动服务
2. 执行基础 API 测试 (fusion-mark-qbk)
3. 执行任务提交测试 (fusion-mark-bl3)
4. 执行任务状态查询测试 (fusion-mark-hm7)

### 阶段 2: 核心功能验证
5. 执行结果下载测试 (fusion-mark-xob)
6. 执行 WebSocket 测试 (fusion-mark-bxp)
7. 执行 E2E 全流程测试 (fusion-mark-5d5)

### 阶段 3: 辅助功能验证
8. 执行任务列表测试 (fusion-mark-4tp)
9. 执行配置管理测试 (fusion-mark-jmt)

### 阶段 4: 稳定性验证
10. 执行错误处理测试 (fusion-mark-3yc)
11. 执行并发性能测试 (fusion-mark-7fk)

### 阶段 5: 文档和自动化
12. 编写自动化测试脚本 (fusion-mark-rr9)

---

## 测试结果记录

每项测试完成后，更新对应 beads issue 的状态:

```bash
# 开始测试
bd update fusion-mark-qbk --status in_progress

# 测试完成
bd close fusion-mark-qbk --reason "测试通过，所有基础 API 功能正常"

# 测试发现问题
bd update fusion-mark-qbk --status blocked
bd comments fusion-mark-qbk "发现问题: ..."
```

---

## 附录

### API 端点汇总

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |
| GET | `/docs` | API 文档 (Swagger) |
| POST | `/api/v1/tasks` | 提交任务 |
| GET | `/api/v1/tasks` | 列出任务 |
| GET | `/api/v1/tasks/{task_id}` | 查询任务状态 |
| GET | `/api/v1/tasks/{task_id}/download` | 下载结果 |
| GET | `/api/v1/config/default` | 获取默认配置 |
| POST | `/api/v1/config` | 更新配置 |
| WS | `/ws/{task_id}` | WebSocket 实时进度 |
