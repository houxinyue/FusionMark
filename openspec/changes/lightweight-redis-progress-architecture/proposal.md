# 轻量化 Redis 进度架构

## Why

当前 Celery Chain 架构过于重量级，引入了大量不必要的复杂性：
- 需要管理 Celery Worker 进程
- 配置复杂（Broker、Backend、队列）
- 部署繁琐（多进程协调）
- 单机部署场景下过度设计

我们需要一个更简单、更轻量的方案，专注于解决核心问题：**进度实时可见**。

## Background

原 Celery Chain 架构（`celery_chain_pipeline/`）过于重量级，不符合当前单机部署场景的需求。

| 问题 | 说明 |
|------|------|
| 架构复杂 | 需要 Redis + Celery Worker + FastAPI 三个组件 |
| 维护成本高 | Celery 配置、队列管理、Worker 监控 |
| 部署繁琐 | 需要启动多个进程，本地开发麻烦 |
| 过度设计 | 单机部署场景不需要分布式能力 |

## 目标

实现轻量化的 Redis 进度架构，替代原 Celery Chain 方案：

- **FastAPI 自身作为 Worker**（后台任务）
- **Redis Hash 存储任务进度**（持久化）
- **Redis PubSub 实时推送 WebSocket**
- **单一进程部署**，简化运维成本

## 设计原则

> **"回归业务本质，去掉繁琐的任务框架"**

1. **简化架构** - 只保留 FastAPI + Redis，去掉 Celery Worker
2. **进度可感知** - LangExtract 阻塞前先发状态通知
3. **失败即标记** - 不自动重试，用户手动重新提交
4. **单机优先** - 当前不考虑分布式，但预留扩展能力

## What Changes

用轻量化的 Redis 进度架构替代 Celery Chain：
- FastAPI 自身作为 Worker（后台任务）
- Redis Hash 存储任务进度（持久化）
- Redis PubSub 实时推送 WebSocket
- 单一进程部署

## Impact

- **架构简化**: 从 3 个组件减少到 2 个（FastAPI + Redis）
- **部署简化**: 单一进程，无需 Worker 管理
- **进度可感知**: LangExtract 阻塞前先发状态通知
- **状态持久化**: 服务重启后任务状态不丢失

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 服务 (单一进程)                    │
│         ┌──────────────────────────────────────┐            │
│         │      BackgroundTasks / asyncio        │            │
│         │   async def process_pdf_task():       │            │
│         │       1. MinerU (有回调) ──► Redis     │            │
│         │       2. LangExtract ──► Redis ⭐      │            │
│         │       3. 高亮渲染 ──► Redis            │            │
│         └──────────────────┬───────────────────┘            │
│                            │ 写入进度                        │
│                            ▼                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Redis (进度看板 + 实时推送)                │   │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │   │
│  │  │ Hash: status:*  │  │ PubSub: pubsub:*         │  │   │
│  │  │ - progress      │  │                          │  │   │
│  │  │ - state         │  │  WebSocket handler 订阅   │  │   │
│  │  │ - message       │  │                          │  │   │
│  │  │ - result        │  │                          │  │   │
│  │  └─────────────────┘  └──────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 进度埋点设计

| 阶段 | 进度 | 状态 | 消息 |
|------|------|------|------|
| 初始化 | 5% | pending | "任务已接收，准备处理..." |
| MinerU 解析 | 10% → 40% | processing | "正在解析 PDF 内容..." |
| LangExtract | **40% → 45%** | processing | **"调用大模型提取实体（约需1-3分钟）..."** |
| LangExtract 内部 | 45% → 85% | processing | 阻塞等待中... |
| 高亮渲染 | 85% → 95% | processing | "正在生成高亮 PDF..." |
| 完成 | 100% | completed | "处理完成！" |
| 失败 | - | failed | "处理失败：xxx" |

## 废弃说明

本方案替代原 **Celery Chain 架构**（fusion-mark-h2f）：
- Celery Chain 规格已归档
- `celery_chain_pipeline/` 目录代码保留供参考，但不再维护

## 关联文档

- `docs/轻量化Redis进度架构设计.md` - 详细设计文档
- `docs/celery_full_pipeline_design.md` - 废弃的原架构（保留参考）
