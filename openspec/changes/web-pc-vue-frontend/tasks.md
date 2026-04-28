# Tasks

## 1. Design
- [x] 确认技术栈（Vue 3 + Vite + TS + Naive UI + Pinia + Vue Router + Axios + PDF.js + @vueuse/core）
- [x] 确认目录结构
- [x] 确认 API 契约（复用现有后端接口，无变更）

## 2. Implementation
- [x] 初始化 Vite + Vue + TypeScript 工程（`pnpm create vite`）
- [x] 安装核心依赖（naive-ui, pinia, vue-router, axios, pdfjs-dist, @vueuse/core）
- [x] 安装工程化依赖（eslint, prettier, vitest, @vue/test-utils, sass）
- [x] 创建全局配置（vite.config.ts / tsconfig.json / .env / .prettierrc / eslint.config.js）
- [x] 创建 src/types/ 类型定义（task.ts, progress.ts, entity.ts）
- [x] 创建 src/api/ 接口层（http.ts, taskApi.ts）
- [x] 创建 src/stores/ Pinia Store（taskStore.ts）
- [x] 创建 src/composables/ 组合式逻辑（usePdfViewer.ts, useTaskWebSocket.ts, useNotification.ts, useDownload.ts）
- [x] 创建 src/constants/ 常量（entityColors.ts, stage.ts）
- [x] 创建 src/utils/ 工具函数（escapeHtml.ts, formatTime.ts, file.ts）
- [x] 创建 src/router/ 路由配置（index.ts）
- [x] 创建 src/styles/ 全局样式（variables.css, reset.css, main.css）
- [x] 创建 src/components/ 业务组件（layout, upload, progress, pdf, entity）
- [x] 创建 src/views/ 页面级组件（ProcessPdfView.vue, TaskHistoryView.vue, ConfigView.vue）
- [x] 创建 App.vue 和 main.ts 入口
- [x] 迁移现有品牌色 CSS 变量到 Naive UI 主题配置

## 3. Validation
- [x] `pnpm install` 安装成功
- [x] `pnpm build` 生产构建成功
- [ ] `pnpm dev` 开发服务器启动无报错（待手动验证）
- [ ] Naive UI 深色主题和品牌色生效（待手动验证）
- [ ] Vite proxy 配置验证（待手动验证）
