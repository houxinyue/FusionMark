# Web-PC Vue 3 前端工程构建

## Problem / Intent

当前 FusionMark 前端为原生 HTML/CSS/JS（`frontend/index.html` + `app.js` + `main.css`），存在以下问题：

- 所有逻辑集中在单个 `app.js`（~964 行），维护成本高
- DOM 操作与状态耦合严重，缺少组件化拆分
- 缺少类型约束（TypeScript）
- 缺少模块化接口层、路由体系、状态管理
- 缺少生产环境构建方案与工程化能力（Lint、Format、Build）

需要构建一个生产级的 Vue 3 前端工程，承载现有的 PDF 处理、WebSocket 实时进度、PDF.js 预览、实体回溯等业务能力。

## Scope

在根目录下新建 `web-pc/` 目录，基于以下技术栈初始化完整前端工程：

- **Vue 3** + **Vite** + **TypeScript**
- **Naive UI**（深色主题组件库）
- **Pinia**（全局状态管理）
- **Vue Router**（前端路由）
- **Axios**（HTTP 请求封装）
- **PDF.js**（PDF 预览渲染）
- **@vueuse/core**（组合式工具集，WebSocket 等）
- **ESLint** + **Prettier** + **Vitest**（工程化）
- **pnpm** 作为包管理器

工程需包含：

1. 完整的推荐目录结构（`src/api/`, `src/components/`, `src/composables/`, `src/stores/`, `src/views/` 等）
2. 核心模块代码（Axios 封装、任务 API、Pinia Store、WebSocket Composable、PDF.js Composable）
3. TypeScript 类型定义（任务、进度、实体）
4. 页面级组件拆分（ProcessPdfView、TaskHistoryView、ConfigView）
5. Vue Router 路由配置
6. Naive UI 深色主题配置
7. Vite dev proxy（`/api` 和 `/ws` 转发到后端）
8. 环境变量配置（`.env.development` / `.env.production`）
9. 保留现有品牌色 CSS 变量（克莱因蓝、爱马仕橙、深色主题）

## Out of Scope

- 后端接口改动
- 业务逻辑功能新增（仅做前端工程化迁移和能力对齐）
- 自动化测试用例编写（保留 Vitest 配置，测试文件仅放示例）
- CI/CD 流水线配置
- 多语言国际化

## Affected Modules

- 新增 `web-pc/` 目录（不影响现有 `frontend/` 目录，原代码保留作为参考）

## Architecture / Design Approach

### 目录结构

```
web-pc/
├─ public/
├─ src/
│  ├─ api/           # Axios 实例 + 任务接口
│  ├─ assets/        # 静态资源
│  ├─ components/    # 通用业务组件
│  │  ├─ layout/
│  │  ├─ upload/
│  │  ├─ progress/
│  │  ├─ pdf/
│  │  └─ entity/
│  ├─ composables/   # 组合式逻辑（PDF.js、WebSocket、通知、下载）
│  ├─ config/        # 前端配置
│  ├─ constants/     # 常量定义（实体颜色、阶段配置）
│  ├─ router/        # Vue Router
│  ├─ stores/        # Pinia 状态管理
│  ├─ styles/        # 全局样式（CSS 变量、reset、主样式）
│  ├─ types/         # TypeScript 类型
│  ├─ utils/         # 工具函数
│  ├─ views/         # 页面级组件
│  ├─ App.vue
│  └─ main.ts
├─ .env.development
├─ .env.production
├─ index.html
├─ package.json
├─ tsconfig.json
├─ tsconfig.app.json
├─ tsconfig.node.json
├─ vite.config.ts
├─ eslint.config.js
└─ .prettierrc
```

### 关键设计决策

1. **渐进式迁移**：保留现有 CSS 品牌变量，Naive UI 主题覆盖与之对齐
2. **状态管理边界**：Pinia 管理全局任务状态；组件局部状态留在组件内
3. **PDF.js 客户端渲染**：`pdfjs-dist` 通过 Vite 方式引入，Worker 独立线程加载
4. **环境变量驱动**：`VITE_API_BASE_URL` / `VITE_WS_BASE_URL` 区分开发和生产环境

## Data or API Contract Changes

无后端 API 变更。前端继续对接现有接口：

- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{taskId}`
- `GET /api/v1/tasks/{taskId}/download`
- `GET /api/v1/tasks/{taskId}/artifacts/langextract_html`
- `WS /ws/{taskId}`

## Risks

| 风险 | 缓解措施 |
|---|---|
| PDF.js 版本升级导致渲染差异 | 使用与当前兼容的版本（4.x），保留旋转处理逻辑 |
| Naive UI 样式与现有深色主题冲突 | 通过 `n-config-provider` 自定义主题覆盖，保留 CSS 变量 |
| 工程初始化后首次构建失败 | 确保 `vite.config.ts` alias 和 tsconfig paths 一致 |

## Validation Plan

1. `cd web-pc; pnpm install` 成功安装所有依赖
2. `pnpm dev` 启动开发服务器，无报错
3. `pnpm build` 生产构建成功，无类型/语法错误
4. 页面能正常加载，Naive UI 深色主题生效
5. Vite proxy 配置正确转发 `/api` 和 `/ws` 到 `localhost:8000`

## Rollback Plan

`web-pc/` 为新增目录，不影响现有代码。如需回退，直接删除 `web-pc/` 目录即可。
