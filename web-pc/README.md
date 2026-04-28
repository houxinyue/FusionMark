# FusionMark Web-PC 前端

FusionMark 的 PC 端前端工程，基于 **Vue 3 + Vite + TypeScript + Naive UI** 构建。

## 技术栈

| 技术 | 版本 | 作用 |
|---|---|---|
| Vue | ^3.5.32 | 前端框架 |
| Vite | ^8.0.10 | 构建与开发服务器 |
| TypeScript | ~6.0.2 | 类型约束 |
| Naive UI | ^2.44.1 | UI 组件库 |
| Pinia | ^3.0.4 | 全局状态管理 |
| Vue Router | ^5.0.6 | 前端路由 |
| Axios | ^1.15.2 | HTTP 请求封装 |
| pdfjs-dist | ^5.6.205 | PDF 在线预览 |

## 当前功能

- URL 文档任务提交：`POST /api/v1/tasks`
- WebSocket 实时进度：`WS /ws/{task_id}`
- 三阶段进度展示：MinerU / LangExtract / Highlight
- 完成态结果下载：`GET /api/v1/tasks/{task_id}/download`
- 中间 PDF 区在线预览高亮 PDF：`GET /api/v1/tasks/{task_id}/artifacts/highlight_pdf`
- 提取结果弹窗：
  - 下载实体 JSONL：`GET /api/v1/tasks/{task_id}/artifacts/entities`
  - iframe 嵌入 LangExtract HTML：`GET /api/v1/tasks/{task_id}/artifacts/langextract_html`

暂未完成：

- 本地文件上传到后端任务接口
- 任务历史页完整联调
- 配置管理页完整联调

## 目录结构

```text
web-pc/
├── public/                  # 静态资源，包含 favicon.svg
├── src/
│   ├── api/                 # 后端接口封装
│   ├── assets/              # Logo 与视觉资源
│   ├── components/          # 业务组件
│   │   ├── layout/          # Header / Footer
│   │   ├── upload/          # URL 提交与上传入口
│   │   ├── progress/        # 进度卡片、阶段列表、日志
│   │   ├── pdf/             # PDF 工具栏与 PDF.js 预览
│   │   └── entity/          # 提取结果入口与弹窗
│   ├── composables/         # WebSocket / PDF.js / 下载等组合逻辑
│   ├── constants/           # 阶段与实体颜色常量
│   ├── router/              # Vue Router
│   ├── stores/              # Pinia store
│   ├── styles/              # 全局样式与设计 token
│   ├── theme/               # Naive UI 主题覆盖
│   ├── types/               # TypeScript 类型
│   └── views/               # 页面级组件
├── package.json
├── pnpm-lock.yaml
└── vite.config.ts
```

## 开发命令

```powershell
pnpm install
pnpm.cmd dev
pnpm.cmd build
pnpm.cmd preview
pnpm.cmd test:dist
pnpm.cmd lint
pnpm.cmd test
```

开发服务器默认运行在：

```text
http://127.0.0.1:5173
```

查看 `dist/` 生产构建效果：

```powershell
pnpm.cmd build
pnpm.cmd test:dist
```

预览地址：

```text
http://127.0.0.1:4173
```

## 环境变量

| 变量 | 开发默认值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | REST API 基础地址 |
| `VITE_WS_BASE_URL` | `ws://localhost:8000` | WebSocket 基础地址 |

## 后端联调

启动后端：

```powershell
uv run uvicorn services.api.server:app --reload --host 0.0.0.0 --port 8000
```

启动前端：

```powershell
cd web-pc
pnpm.cmd dev
```

Vite 开发代理：

| 前端路径 | 代理目标 |
|---|---|
| `/api` | `http://localhost:8000` |
| `/ws` | `ws://localhost:8000` |

## 主链路

```text
输入文档 URL
  -> POST /api/v1/tasks
  -> 写入 task_id
  -> 连接 WS /ws/{task_id}
  -> 更新 MinerU / LangExtract / Highlight 进度
  -> completed
  -> 加载高亮 PDF artifact
  -> 提供结果 PDF 下载与提取结果查看
```

## 视觉主题

当前采用浅色文档工作台风格：

- 主底色：白色 / 浅蓝灰
- 文字：灰蓝色
- 主操作与强调：Logo 呼应橘色 `#f97316` / `#fb923c`
- PDF 空态：FusionMark 核心轨道图，表达 MinerU 提取、LangExtract 识别、FusionMark 输出高亮 PDF

## 注意事项

- 推荐 Node.js 18+。
- 包管理器使用 `pnpm`。
- Windows PowerShell 下优先使用 `pnpm.cmd`，避免 `.ps1` 执行策略问题。
- PDF.js 的文档对象使用 `shallowRef + markRaw` 保存，避免 Vue 代理破坏 PDF.js 私有字段。
- LangExtract HTML 使用 iframe `sandbox="allow-same-origin allow-scripts"` 嵌入，以支持官方可视化脚本执行。
