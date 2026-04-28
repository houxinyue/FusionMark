# Web-PC 前后端主链路联调

## Problem / Intent

`web-pc` 已完成 Vue 3 前端工程与 UI v0，但当前前端仍停留在视觉骨架和部分 API helper 阶段：URL 提交、任务状态、WebSocket 进度、完成态下载、产物入口还没有串成可用主链路。

后端 `services/api/server.py` 已提供任务创建、任务查询、任务列表、下载、Artifacts 和 WebSocket 进度接口。本次变更目标是先完成最小可用联调闭环：

```text
输入文档 URL -> 创建任务 -> 连接 WebSocket -> 展示进度 -> 完成后下载结果
```

## Scope

本次只做第一阶段主链路联调：

- 接入 `POST /api/v1/tasks`，让 `UrlSubmit.vue` 可以提交 URL 任务。
- 在任务创建成功后写入 Pinia store，并连接 `WS /ws/{task_id}`。
- 适配后端 WebSocket 消息结构，将后端任务快照规范化为前端 `TaskProgress`。
- 在任务完成/失败时正确更新右侧状态区。
- 接入结果下载入口：`GET /api/v1/tasks/{task_id}/download`。
- 增加必要的 API helper 和类型定义，为后续 artifacts/history/config 联调预留稳定接口。
- 保留当前 UI v0 布局，不做新的视觉重构。

## Out of Scope

- 不实现本地文件上传到后端，因为当前后端主任务接口以 `document_url` 为输入。
- 不完整实现任务历史页。
- 不完整实现配置管理页。
- 不实现高亮 PDF 在线预览，只先提供完成态下载入口。
- 不改后端任务处理逻辑、Redis 进度存储、MinerU/LangExtract pipeline。
- 不引入新的前端运行时依赖。

## Affected Modules

- `web-pc/src/api/taskApi.ts`
- `web-pc/src/stores/taskStore.ts`
- `web-pc/src/composables/useTaskWebSocket.ts`
- `web-pc/src/components/upload/UrlSubmit.vue`
- `web-pc/src/components/progress/ProgressCard.vue`
- `web-pc/src/components/progress/ProgressLogs.vue`
- `web-pc/src/components/progress/StageList.vue`
- `web-pc/src/components/entity/EntityTraceButton.vue`
- `web-pc/src/types/task.ts`
- `web-pc/src/types/progress.ts`
- Optional: `web-pc/src/composables/useDownload.ts`

## Interface Alignment

### Create Task

Frontend submits:

```json
{
  "document_url": "https://example.com/file.pdf",
  "model": "vlm",
  "enable_ocr": true,
  "enable_formula": true,
  "enable_table": true,
  "language": "ch"
}
```

Backend responds with `TaskResponse`:

```json
{
  "task_id": "...",
  "status": "pending",
  "message": "...",
  "created_at": "..."
}
```

### WebSocket Message

Backend sends:

```json
{
  "type": "progress",
  "data": {
    "task_id": "...",
    "status": "processing",
    "stage": "mineru",
    "overall_progress": 30,
    "mineru": { "state": "running", "progress": 60, "logs": [] },
    "extraction": { "state": "pending", "progress": 0, "logs": [] },
    "highlight": { "state": "pending", "progress": 0, "logs": [] },
    "message": "..."
  }
}
```

Frontend will normalize both `connected` and `progress` payloads through a single store action.

## Architecture / Design Approach

### Store-first Integration

The task store becomes the single owner of task state transitions:

- `startTask(taskId)`
- `applyTaskSnapshot(snapshot)`
- `appendStageLogs(progress)`
- `completeTask(result)`
- `failTask(message)`
- `reset()`

Components should not manually mutate progress/status except through store actions.

### WebSocket Fallback

WebSocket errors should not immediately mark a task failed. The frontend should:

1. close the socket,
2. call `GET /api/v1/tasks/{task_id}`,
3. apply the latest server snapshot,
4. mark failed only if backend status is `failed` or the fallback query fails.

### Download Entry

When task status is `completed`, the inspect rail shows a result action using:

```ts
getTaskDownloadUrl(taskId)
```

The first version opens the URL directly in a new browser navigation/download action.

## Data or API Contract Changes

No backend contract change is planned.

Frontend type definitions will be expanded to reflect the backend response shape more accurately.

## Risks

| Risk | Mitigation |
|---|---|
| WebSocket payload contains missing stage fields | Normalizer supplies default pending stage objects |
| Backend task fails before WebSocket connects | Query task detail after create and on WS error |
| Result download is unavailable because task has not completed | Only show download action after `completed`; backend errors remain visible |
| Logs duplicate across repeated progress messages | Use simple de-duplication key based on stage + text |

## Validation Plan

- `pnpm.cmd build` in `web-pc`.
- Backend health check: `GET http://localhost:8000/health`.
- Submit one valid PDF URL from the UI.
- Confirm `task_id` is stored and WebSocket connects.
- Confirm progress card updates overall progress and three stages.
- Confirm completed status shows download entry.
- Confirm failed task displays failure state instead of staying in processing.

## Rollback Plan

All changes are frontend integration code. Roll back by reverting the implementation commit. No backend data migration or API change is involved.
