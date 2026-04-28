# FusionMark Web-PC 前端

FusionMark 的 PC 端前端工程，基于 **Vue 3 + Vite + TypeScript + Naive UI** 构建。

## 技术栈

| 技术 | 版本 | 作用 |
|---|---|---|
| Vue | ^3.5.32 | 渐进式前端框架 |
| Vite | ^8.0.10 | 构建工具 |
| TypeScript | ~6.0.2 | 类型约束 |
| Naive UI | ^2.44.1 | UI 组件库（深色主题） |
| Pinia | ^3.0.4 | 全局状态管理 |
| Vue Router | ^5.0.6 | 前端路由 |
| Axios | ^1.15.2 | HTTP 请求封装 |
| pdfjs-dist | ^5.6.205 | PDF 预览渲染 |
| @vueuse/core | ^14.2.1 | 组合式工具集 |
| Vitest | ^4.1.5 | 单元测试框架 |
| ESLint | ^10.2.1 | 代码质量检查 |
| Prettier | ^3.8.3 | 代码格式化 |

## 目录结构

```
web-pc/
├─ public/                  # 静态资源
├─ src/
│  ├─ api/                  # 后端接口层
│  │  ├─ http.ts            # Axios 实例与拦截器
│  │  └─ taskApi.ts         # 任务相关接口
│  ├─ assets/               # 图片等静态资源
│  ├─ components/           # 通用业务组件
│  │  ├─ layout/            # 布局组件（Header / Footer）
│  │  ├─ upload/            # 上传相关（PdfUpload / UrlSubmit）
│  │  ├─ progress/          # 进度展示（ProgressCard / StageList / ProgressLogs）
│  │  ├─ pdf/               # PDF 预览（PdfViewer / PdfToolbar）
│  │  └─ entity/            # 实体回溯（EntityTraceButton / EntityModal）
│  ├─ composables/          # 组合式逻辑（PDF.js / WebSocket / 通知 / 下载）
│  ├─ config/               # 前端配置
│  ├─ constants/            # 常量定义（实体颜色、阶段标签）
│  ├─ router/               # Vue Router 路由配置
│  ├─ stores/               # Pinia 状态管理
│  ├─ styles/               # 全局样式（CSS 变量、reset、主样式）
│  ├─ types/                # TypeScript 类型定义
│  ├─ utils/                # 工具函数
│  ├─ views/                # 页面级组件
│  │  ├─ ProcessPdfView.vue # PDF 处理主页面
│  │  ├─ TaskHistoryView.vue# 任务历史
│  │  └─ ConfigView.vue     # 配置管理
│  ├─ App.vue               # 根组件（Naive UI 主题 Provider）
│  └─ main.ts               # 应用入口
├─ .env.development         # 开发环境变量
├─ .env.production          # 生产环境变量
├─ vite.config.ts           # Vite 配置（含 dev proxy）
├─ tsconfig.app.json        # TypeScript 应用配置
├─ package.json             # 依赖与脚本
└─ README.md                # 本文件
```

## 开发命令

```bash
# 安装依赖
pnpm install

# 启动开发服务器（port 5173，自动代理 /api 和 /ws 到 localhost:8000）
pnpm dev

# 生产构建
pnpm build

# 预览生产包
pnpm preview

# 代码检查
pnpm lint

# 代码格式化
pnpm format

# 运行测试
pnpm test
```

## 环境变量

| 变量 | 开发默认值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | REST API 基础地址 |
| `VITE_WS_BASE_URL` | `ws://localhost:8000` | WebSocket 基础地址 |

## 路由规划

| 路由 | 页面 | 说明 |
|---|---|---|
| `/` | ProcessPdfView | PDF 处理主页面 |
| `/history` | TaskHistoryView | 任务历史 |
| `/config` | ConfigView | 解析与高亮配置 |

## 主题配色

采用**深色科技风**，品牌色：

- **克莱因蓝** `#002FA7` — 主色调（按钮、高亮、进度）
- **爱马仕橙** `#FF6600` — 辅助色（警告、强调）

## 后端接口对接

前端默认对接以下接口：

```
POST /api/v1/tasks
GET  /api/v1/tasks/{taskId}
GET  /api/v1/tasks/{taskId}/download
GET  /api/v1/tasks/{taskId}/artifacts/langextract_html
WS   /ws/{taskId}
```

开发环境下，Vite dev server 会自动将 `/api` 和 `/ws` 代理到 `localhost:8000`。

## 注意事项

- **Node.js 版本**: 建议 18+
- **包管理器**: 必须使用 **pnpm**（`.npmrc` 中配置了 `node-linker=hoisted` 以兼容 exFAT 文件系统）
- **PDF.js Worker**: `pdfjs-dist` 的 Worker 通过 Vite 的 `new URL(..., import.meta.url)` 方式加载
