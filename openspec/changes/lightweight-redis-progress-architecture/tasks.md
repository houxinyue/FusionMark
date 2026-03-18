# 轻量化 Redis 进度架构 - Tasks

## Phase 1: 核心组件开发 (1天)

### 1.1 进度存储模块
- [ ] 创建 `progress_store.py`
  - [ ] `RedisProgressStore` 类
  - [ ] `create_task()` - 初始化任务状态
  - [ ] `update_progress()` - 更新进度 + PubSub 发布
  - [ ] `get_task()` - 查询任务状态
  - [ ] `KEY_PREFIX` 常量定义

### 1.2 WebSocket 适配器
- [ ] 创建 `websocket_handler.py`
  - [ ] `WebSocketProgressHandler` 类
  - [ ] 订阅 Redis PubSub
  - [ ] 实时推送到前端
  - [ ] 连接断开处理

### 1.3 配置管理
- [ ] 添加 Redis 连接配置到 `.env`
  - `REDIS_URL=redis://localhost:6379`
- [ ] 更新 `requirements.txt`
  - `redis>=5.0.1`
  - `aioredis>=2.9.3`

## Phase 2: 后台任务改造 (1天)

### 2.1 异步化改造
- [ ] 重构 `process_pdf_task` 为 `async def`
- [ ] 使用 `asyncio.to_thread()` 包装阻塞调用
  - MinerU 解析
  - LangExtract 提取
  - 高亮渲染
- [ ] 接入 `RedisProgressStore` 替代内存存储

### 2.2 进度埋点
- [ ] MinerU 阶段进度回调集成
  - [ ] 页码进度实时更新 (10% → 40%)
  - [ ] 轮询状态映射到进度百分比
- [ ] LangExtract 阻塞前状态通知
  - [ ] ⭐ 关键：进入前更新 "调用大模型中（约需1-3分钟）..."
  - [ ] 进度从 45% 跳到 85%（完成后）
- [ ] 高亮渲染进度模拟 (85% → 95%)

### 2.3 错误处理
- [ ] 异常捕获与状态标记为 `failed`
- [ ] 错误信息持久化到 Redis
- [ ] WebSocket 推送失败通知
- [ ] 日志记录完善

## Phase 3: API 层改造 (0.5天)

- [ ] 更新 `/api/v1/tasks` POST 接口
  - [ ] 使用 `asyncio.create_task()` 启动后台任务
  - [ ] 立即返回 task_id
  - [ ] 初始化 Redis 任务状态
- [ ] 更新 `/api/v1/tasks/{task_id}` GET 接口
  - [ ] 从 Redis 读取任务状态
  - [ ] 保持 API 响应格式兼容
- [ ] 更新 `/ws/{task_id}` WebSocket 接口
  - [ ] 接入新的 WebSocketProgressHandler
  - [ ] 处理连接、订阅、推送、断开

## Phase 4: 测试验证 (1天)

- [ ] 本地 Redis + FastAPI 联调测试
- [ ] WebSocket 实时进度推送测试
- [ ] 任务中断/重启恢复测试
- [ ] LangExtract 长时间等待场景测试
- [ ] 并发任务处理测试

## Phase 5: 废弃清理 (0.5天)

- [ ] 标记 `celery_chain_pipeline/` 目录为废弃
  - [ ] 添加 README.md 说明废弃状态
  - [ ] 代码中添加 deprecation 注释
- [ ] 更新项目文档
  - [ ] 更新 README.md 架构说明
  - [ ] 更新 AGENTS.md 相关说明
- [ ] 清理不再使用的依赖
  - [ ] 从 requirements.txt 移除 celery

## 验收标准

1. ✅ 单进程部署（FastAPI + Redis）
2. ✅ 任务进度实时可见（WebSocket 推送）
3. ✅ LangExtract 等待可感知（"调用大模型中..."）
4. ✅ 服务重启后任务状态不丢失（Redis 持久化）
5. ✅ 失败任务可重新提交
