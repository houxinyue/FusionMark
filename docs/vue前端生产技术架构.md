# FusionMark 前端技术架构转型方案

> 目标：将当前无框架的原生 HTML / CSS / JavaScript 前端，升级为基于 Vue 3 + Vite + TypeScript + Naive UI 的生产级前端工程。

---

## 1. 当前项目现状

当前 FusionMark 前端主要由以下文件组成：

```txt
index.html
main.css
app.js
```

当前页面已经具备完整的业务雏形，包括：

- PDF 文件选择与拖拽上传
- PDF URL 输入并提交任务
- 任务进度展示
- WebSocket 实时日志监听
- PDF.js 预览
- 下载处理结果
- LangExtract 实体回溯弹窗
- 深色主题 UI

但是当前实现存在一些典型问题：

- 所有逻辑集中在一个 `app.js` 中，维护成本会越来越高
- DOM 操作较多，状态和视图耦合严重
- 缺少模块化接口层
- 缺少类型约束
- 缺少路由体系
- 缺少统一状态管理
- 缺少生产环境构建方案
- 缺少组件复用机制
- 缺少规范化目录结构
- 缺少测试、格式化、Lint 等工程化能力

因此建议升级为 Vue 3 生产级前端架构。

---

## 2. 推荐技术栈

### 2.1 核心框架

| 技术 | 作用 |
|---|---|
| Vue 3 | 前端核心框架 |
| Vite | 构建工具 |
| TypeScript | 类型约束 |
| Naive UI | UI 组件库 |
| Pinia | 全局状态管理 |
| Vue Router | 前端路由 |
| Axios | HTTP 请求 |
| PDF.js | PDF 预览渲染 |

### 2.2 工程化工具

| 技术 | 作用 |
|---|---|
| ESLint | 代码质量检查 |
| Prettier | 代码格式化 |
| Vitest | 单元测试 |
| Vue Test Utils | Vue 组件测试 |
| pnpm | 包管理工具 |

### 2.3 推荐组合

```txt
Vue 3 + Vite + TypeScript + Naive UI + Pinia + Vue Router + Axios + PDF.js
```

该组合适合 FusionMark 这种“任务型 + 文件处理 + 实时进度 + PDF 预览”的前端项目。

---

## 3. 新项目目录结构

推荐目录如下：

```txt
fusionmark-web/
├─ public/
│  └─ favicon.ico
│
├─ src/
│  ├─ api/                         # 后端接口层
│  │  ├─ http.ts                   # Axios 实例
│  │  └─ taskApi.ts                # 任务相关接口
│  │
│  ├─ assets/                      # 静态资源
│  │  └─ images/
│  │
│  ├─ components/                  # 通用业务组件
│  │  ├─ layout/
│  │  │  ├─ AppHeader.vue
│  │  │  └─ AppFooter.vue
│  │  │
│  │  ├─ upload/
│  │  │  ├─ PdfUpload.vue
│  │  │  └─ UrlSubmit.vue
│  │  │
│  │  ├─ progress/
│  │  │  ├─ ProgressCard.vue
│  │  │  ├─ StageList.vue
│  │  │  └─ ProgressLogs.vue
│  │  │
│  │  ├─ pdf/
│  │  │  ├─ PdfViewer.vue
│  │  │  └─ PdfToolbar.vue
│  │  │
│  │  └─ entity/
│  │     ├─ EntityTraceButton.vue
│  │     └─ EntityModal.vue
│  │
│  ├─ composables/                 # 组合式逻辑
│  │  ├─ usePdfViewer.ts
│  │  ├─ useTaskWebSocket.ts
│  │  ├─ useNotification.ts
│  │  └─ useDownload.ts
│  │
│  ├─ config/                      # 前端配置
│  │  └─ appConfig.ts
│  │
│  ├─ constants/                   # 常量定义
│  │  ├─ entityColors.ts
│  │  └─ stage.ts
│  │
│  ├─ router/                      # 路由
│  │  └─ index.ts
│  │
│  ├─ stores/                      # Pinia 状态管理
│  │  └─ taskStore.ts
│  │
│  ├─ styles/                      # 全局样式
│  │  ├─ variables.css
│  │  ├─ reset.css
│  │  └─ main.css
│  │
│  ├─ types/                       # TypeScript 类型
│  │  ├─ task.ts
│  │  ├─ progress.ts
│  │  └─ entity.ts
│  │
│  ├─ utils/                       # 工具函数
│  │  ├─ escapeHtml.ts
│  │  ├─ formatTime.ts
│  │  └─ file.ts
│  │
│  ├─ views/                       # 页面级组件
│  │  ├─ ProcessPdfView.vue
│  │  ├─ TaskHistoryView.vue
│  │  └─ ConfigView.vue
│  │
│  ├─ App.vue
│  └─ main.ts
│
├─ .env.development
├─ .env.production
├─ .eslintrc.cjs
├─ .prettierrc
├─ index.html
├─ package.json
├─ tsconfig.json
└─ vite.config.ts
```

---

## 4. 页面模块拆分

### 4.1 页面级结构

当前 `index.html` 可以拆成：

```txt
App.vue
├─ AppHeader.vue
├─ router-view
└─ AppFooter.vue
```

主页面为：

```txt
ProcessPdfView.vue
├─ 左侧操作面板
│  ├─ PdfUpload.vue
│  ├─ UrlSubmit.vue
│  ├─ ProgressCard.vue
│  │  ├─ StageList.vue
│  │  └─ ProgressLogs.vue
│  └─ EntityTraceButton.vue
│
├─ 右侧 PDF 面板
│  ├─ PdfToolbar.vue
│  └─ PdfViewer.vue
│
└─ EntityModal.vue
```

---

## 5. 核心模块职责

### 5.1 api/http.ts

统一封装 Axios。

职责：

- 设置 `baseURL`
- 设置请求超时
- 统一请求拦截
- 统一响应拦截
- 统一错误处理

示例：

```ts
import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

http.interceptors.response.use(
  response => response.data,
  error => {
    return Promise.reject(error)
  },
)
```

---

### 5.2 api/taskApi.ts

封装任务相关接口。

职责：

- 创建任务
- 查询任务详情
- 获取下载地址
- 获取 LangExtract HTML

示例：

```ts
import { http } from './http'
import type { CreateTaskPayload, TaskDetail } from '@/types/task'

export function createTask(payload: CreateTaskPayload) {
  return http.post<{ task_id: string }>('/api/v1/tasks', payload)
}

export function getTaskDetail(taskId: string) {
  return http.get<TaskDetail>(`/api/v1/tasks/${taskId}`)
}

export function getTaskDownloadUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/download`
}

export function getLangExtractHtmlUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/artifacts/langextract_html`
}
```

---

### 5.3 stores/taskStore.ts

使用 Pinia 管理任务状态。

职责：

- 当前任务 ID
- 当前状态
- 当前进度
- 当前阶段
- 阶段日志
- 任务结果
- 是否处理中
- LangExtract HTML 地址

示例状态：

```ts
import { defineStore } from 'pinia'
import type { TaskProgress, TaskStatus } from '@/types/task'

export const useTaskStore = defineStore('task', {
  state: () => ({
    currentTaskId: null as string | null,
    status: 'pending' as TaskStatus,
    progress: null as TaskProgress | null,
    isProcessing: false,
    logs: [] as string[],
    entityArtifactUrl: null as string | null,
  }),

  actions: {
    setTaskId(taskId: string) {
      this.currentTaskId = taskId
    },

    reset() {
      this.currentTaskId = null
      this.status = 'pending'
      this.progress = null
      this.isProcessing = false
      this.logs = []
      this.entityArtifactUrl = null
    },
  },
})
```

---

### 5.4 composables/useTaskWebSocket.ts

封装 WebSocket 逻辑。

职责：

- 建立 WebSocket 连接
- 接收任务进度
- 处理心跳
- 处理失败状态
- 处理完成状态
- 自动关闭连接
- 页面卸载时清理连接

示例：

```ts
import { onBeforeUnmount } from 'vue'
import { useTaskStore } from '@/stores/taskStore'

export function useTaskWebSocket() {
  const taskStore = useTaskStore()
  let ws: WebSocket | null = null

  function connect(taskId: string) {
    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL
    ws = new WebSocket(`${wsBaseUrl}/ws/${taskId}`)

    ws.onmessage = event => {
      const data = JSON.parse(event.data)

      if (data.type === 'progress' || data.type === 'connected') {
        taskStore.progress = data.data.progress
        taskStore.status = data.data.status
      }
    }

    ws.onerror = () => {
      taskStore.status = 'failed'
    }
  }

  function close() {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  onBeforeUnmount(() => {
    close()
  })

  return {
    connect,
    close,
  }
}
```

---

### 5.5 composables/usePdfViewer.ts

封装 PDF.js。

职责：

- 初始化 PDF.js worker
- 加载 PDF
- 渲染指定页
- 上一页
- 下一页
- 放大
- 缩小
- 页码跳转
- 销毁 PDF 对象

建议把当前 `loadPDF`、`renderPage`、`updatePageInfo` 迁移到这里。

示例：

```ts
import { ref } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

export function usePdfViewer() {
  const pdfDocument = ref<any>(null)
  const currentPage = ref(1)
  const totalPages = ref(0)
  const zoomLevel = ref(1)

  async function loadPdf(url: string) {
    const loadingTask = pdfjsLib.getDocument(url)
    pdfDocument.value = await loadingTask.promise
    totalPages.value = pdfDocument.value.numPages
  }

  async function renderPage(canvas: HTMLCanvasElement, pageNumber = currentPage.value) {
    if (!pdfDocument.value) return

    const page = await pdfDocument.value.getPage(pageNumber)
    const viewport = page.getViewport({ scale: zoomLevel.value })
    const context = canvas.getContext('2d')

    if (!context) return

    canvas.width = viewport.width
    canvas.height = viewport.height

    await page.render({
      canvasContext: context,
      viewport,
    }).promise

    currentPage.value = pageNumber
  }

  return {
    pdfDocument,
    currentPage,
    totalPages,
    zoomLevel,
    loadPdf,
    renderPage,
  }
}
```

---

## 6. 路由设计

### 6.1 页面规划

| 路由 | 页面 | 说明 |
|---|---|---|
| `/` | ProcessPdfView | PDF 处理主页面 |
| `/history` | TaskHistoryView | 任务历史 |
| `/config` | ConfigView | 解析与高亮配置 |

### 6.2 router/index.ts

```ts
import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'ProcessPdf',
      component: () => import('@/views/ProcessPdfView.vue'),
    },
    {
      path: '/history',
      name: 'TaskHistory',
      component: () => import('@/views/TaskHistoryView.vue'),
    },
    {
      path: '/config',
      name: 'Config',
      component: () => import('@/views/ConfigView.vue'),
    },
  ],
})
```

---

## 7. 环境变量设计

### 7.1 .env.development

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### 7.2 .env.production

```env
VITE_API_BASE_URL=https://your-domain.com
VITE_WS_BASE_URL=wss://your-domain.com
```

### 7.3 为什么不要写死 localhost

当前原生 JS 中写死了：

```js
API_BASE_URL: 'http://localhost:8000'
WS_BASE_URL: 'ws://localhost:8000'
```

这在本地开发可以工作，但部署到服务器后，用户浏览器中的 `localhost` 指的是用户自己的电脑，不是你的后端服务器。

因此生产项目必须使用环境变量区分开发和生产环境。

---

## 8. Naive UI 使用方案

### 8.1 安装

```bash
pnpm add naive-ui
pnpm add -D vfonts
```

### 8.2 main.ts 引入

```ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'
import { router } from './router'
import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

app.mount('#app')
```

### 8.3 App.vue 全局 Provider

```vue
<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-loading-bar-provider>
          <router-view />
        </n-loading-bar-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme, type GlobalThemeOverrides } from 'naive-ui'

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#002FA7',
    primaryColorHover: '#1a4fc7',
    primaryColorPressed: '#001f7a',
    warningColor: '#FF6600',
  },
}
</script>
```

---

## 9. 样式迁移方案

当前 `main.css` 不建议完全丢弃，可以分阶段迁移。

### 9.1 第一阶段：保留 CSS 变量

保留你的品牌色：

```css
:root {
  --klein-blue: #002FA7;
  --klein-blue-light: #1a4fc7;
  --klein-blue-dark: #001f7a;
  --hermes-orange: #FF6600;
  --hermes-orange-light: #ff8533;

  --bg-primary: #1A1A2E;
  --bg-secondary: #16213E;
  --bg-tertiary: #0F3460;

  --text-primary: #FFFFFF;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-muted: rgba(255, 255, 255, 0.5);
}
```

### 9.2 第二阶段：组件内 scoped CSS

例如：

```vue
<style scoped>
.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-md);
}
</style>
```

### 9.3 第三阶段：Naive UI 替换基础组件

可以逐步替换：

| 当前元素 | Naive UI |
|---|---|
| button | n-button |
| input | n-input |
| modal | n-modal |
| notification | n-message / n-notification |
| progress | n-progress |
| card | n-card |
| tabs | n-tabs |
| table | n-data-table |

---

## 10. TypeScript 类型设计

### 10.1 types/task.ts

```ts
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type StageName = 'mineru' | 'extraction' | 'highlight'

export type StageState = 'pending' | 'running' | 'completed' | 'failed' | 'done'

export interface StageProgress {
  state: StageState
  progress: number
  logs: string[]
}

export interface TaskProgress {
  stage: StageName | 'pending' | 'completed' | 'failed'
  stage_progress: number
  overall_progress: number
  mineru: StageProgress
  extraction: StageProgress
  highlight: StageProgress
}

export interface TaskResult {
  output_path?: string
  category_counts?: Record<string, number>
}

export interface TaskDetail {
  task_id: string
  status: TaskStatus
  message?: string
  progress?: TaskProgress
  result?: TaskResult
}

export interface CreateTaskPayload {
  document_url: string
  model?: string
  enable_ocr?: boolean
  enable_formula?: boolean
  enable_table?: boolean
  language?: string
  output_filename?: string | null
  custom_title?: string | null
  custom_prompt?: string | null
}
```

---

## 11. 业务流程设计

### 11.1 URL 提交流程

```txt
用户输入 PDF URL
        ↓
UrlSubmit.vue 校验 URL
        ↓
调用 createTask
        ↓
保存 taskId 到 Pinia
        ↓
连接 WebSocket
        ↓
实时更新 progressStore
        ↓
ProgressCard 自动刷新
        ↓
任务完成
        ↓
显示下载按钮
        ↓
加载 PDF 预览
        ↓
启用 LangExtract 实体回溯按钮
```

### 11.2 PDF 本地预览流程

```txt
用户选择 PDF 文件
        ↓
PdfUpload.vue 获取 File
        ↓
URL.createObjectURL(file)
        ↓
PdfViewer.vue 加载 PDF
        ↓
渲染第一页
        ↓
支持上一页 / 下一页 / 缩放
        ↓
页面卸载或切换文件时 revokeObjectURL
```

### 11.3 WebSocket 流程

```txt
connect(taskId)
        ↓
收到 connected
        ↓
渲染初始状态
        ↓
收到 progress
        ↓
更新任务状态
        ↓
状态为 completed
        ↓
关闭连接 / 显示结果
        ↓
状态为 failed
        ↓
关闭连接 / 显示错误
```

---

## 12. 组件设计建议

### 12.1 ProcessPdfView.vue

只负责布局和组合组件，不写复杂业务逻辑。

```vue
<template>
  <div class="process-page">
    <section class="panel panel-left">
      <PdfUpload />
      <UrlSubmit />
      <ProgressCard />
      <EntityTraceButton />
    </section>

    <section class="panel panel-right">
      <PdfToolbar />
      <PdfViewer />
    </section>

    <EntityModal />
  </div>
</template>
```

---

### 12.2 UrlSubmit.vue

职责：

- 输入 PDF URL
- 校验空值
- 创建任务
- 启动 WebSocket

不应该负责进度 UI。

---

### 12.3 ProgressCard.vue

职责：

- 展示总进度
- 展示当前状态
- 引入 StageList
- 引入 ProgressLogs

不应该直接请求接口。

---

### 12.4 PdfViewer.vue

职责：

- 接收 PDF URL
- 调用 usePdfViewer
- 渲染 canvas

不应该直接处理任务状态。

---

### 12.5 EntityModal.vue

职责：

- 打开弹窗
- 加载 LangExtract HTML
- iframe 展示
- fallback 展示分类统计

---

## 13. 状态管理边界

### 13.1 应该放入 Pinia 的状态

- 当前 taskId
- 任务状态
- 任务进度
- 任务日志
- 任务结果
- 下载地址
- LangExtract HTML 地址

### 13.2 不建议放入 Pinia 的状态

- 当前输入框临时内容
- 弹窗局部开关
- 组件内部 hover 状态
- canvas context
- 临时 File 对象

PDF 当前页和缩放比例可以根据情况选择：

- 如果多个组件都要用，放 Pinia
- 如果只在 PdfViewer / PdfToolbar 之间使用，可以放 composable

---

## 14. 安全性改造

### 14.1 实体文本必须转义

当前原生 JS 中实体文本直接拼接 HTML，迁移后应避免 `v-html`。

推荐：

```vue
<n-tag>{{ entity.text }}</n-tag>
```

Vue 默认会对插值内容进行转义。

### 14.2 LangExtract HTML 使用 iframe

LangExtract 官方 HTML 结果建议继续使用 iframe 隔离展示。

如果后端返回 HTML，不建议直接插入主页面 DOM。

推荐：

```vue
<iframe :srcdoc="htmlContent" sandbox="allow-same-origin"></iframe>
```

如不需要脚本执行，不要加 `allow-scripts`。

### 14.3 URL 校验

提交前至少校验：

- 是否为空
- 是否是合法 URL
- 是否 http / https
- 是否可能是 PDF 链接

---

## 15. 开发命令

### 15.1 初始化项目

```bash
pnpm create vite fusionmark-web --template vue-ts
cd fusionmark-web
```

### 15.2 安装依赖

```bash
pnpm add naive-ui pinia vue-router axios pdfjs-dist
pnpm add -D eslint prettier vitest @vue/test-utils sass
```

### 15.3 启动开发环境

```bash
pnpm dev
```

### 15.4 构建生产包

```bash
pnpm build
```

### 15.5 本地预览生产包

```bash
pnpm preview
```

---

## 16. Vite 配置建议

### 16.1 vite.config.ts

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

开发环境可以使用 Vite proxy，减少跨域配置压力。

---

## 17. 后端接口适配建议

当前前端默认依赖以下接口：

```txt
POST /api/v1/tasks
GET  /api/v1/tasks/{taskId}
GET  /api/v1/tasks/{taskId}/download
GET  /api/v1/tasks/{taskId}/artifacts/langextract_html
WS   /ws/{taskId}
```

建议后端 WebSocket 数据结构统一为：

```json
{
  "type": "progress",
  "data": {
    "task_id": "xxx",
    "status": "processing",
    "message": "MinerU 解析中",
    "progress": {
      "stage": "mineru",
      "stage_progress": 30,
      "overall_progress": 15,
      "mineru": {
        "state": "running",
        "progress": 30,
        "logs": ["开始解析 PDF"]
      },
      "extraction": {
        "state": "pending",
        "progress": 0,
        "logs": []
      },
      "highlight": {
        "state": "pending",
        "progress": 0,
        "logs": []
      }
    }
  }
}
```

---

## 18. 迁移步骤

### 阶段一：搭建 Vue 工程

目标：先让新项目跑起来。

任务：

- 创建 Vue 3 + Vite + TypeScript 项目
- 安装 Naive UI
- 安装 Pinia、Router、Axios、PDF.js
- 配置环境变量
- 配置基础路由
- 迁移全局样式变量

---

### 阶段二：迁移静态页面

目标：先复刻当前 UI。

任务：

- 拆分 AppHeader
- 拆分 AppFooter
- 创建 ProcessPdfView
- 拆分上传区
- 拆分进度卡片
- 拆分 PDF 预览区域
- 拆分实体回溯弹窗

此阶段可以先不接接口。

---

### 阶段三：迁移业务逻辑

目标：让页面恢复当前功能。

任务：

- 迁移 submitTask 到 taskApi
- 迁移 WebSocket 到 useTaskWebSocket
- 迁移 PDF.js 到 usePdfViewer
- 迁移下载逻辑到 useDownload
- 迁移通知为 Naive UI message
- 迁移任务状态到 Pinia

---

### 阶段四：完善交互能力

目标：补齐当前原生项目缺失能力。

任务：

- 上一页 / 下一页
- 页码跳转
- 放大 / 缩小
- 任务失败重试
- WebSocket 断线提示
- 下载异常提示
- 本地 PDF ObjectURL 释放
- PDF 加载 loading 状态

---

### 阶段五：生产化优化

目标：适合部署和长期维护。

任务：

- ESLint + Prettier
- Vitest 单元测试
- 路由懒加载
- 错误边界处理
- API 错误统一处理
- 生产环境变量
- Nginx 部署配置
- Docker 构建配置

---

## 19. 推荐首批组件迁移顺序

建议按以下顺序迁移：

```txt
1. AppHeader.vue
2. AppFooter.vue
3. ProcessPdfView.vue
4. UrlSubmit.vue
5. ProgressCard.vue
6. StageList.vue
7. ProgressLogs.vue
8. PdfToolbar.vue
9. PdfViewer.vue
10. EntityModal.vue
11. taskStore.ts
12. taskApi.ts
13. useTaskWebSocket.ts
14. usePdfViewer.ts
```

原因：

- 先迁移 UI，风险最小
- 再迁移状态，便于调试
- 最后迁移复杂的 WebSocket 和 PDF.js

---

## 20. 部署建议

### 20.1 构建产物

执行：

```bash
pnpm build
```

生成：

```txt
dist/
```

### 20.2 Nginx 部署示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 21. Docker 部署建议

### 21.1 Dockerfile

```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## 22. 最终目标架构图

```txt
用户浏览器
   ↓
Vue 3 前端应用
   ↓
ProcessPdfView
   ├─ UrlSubmit
   ├─ ProgressCard
   ├─ PdfViewer
   └─ EntityModal
   ↓
Pinia Task Store
   ↓
API Layer / WebSocket Layer
   ↓
FusionMark Backend
   ├─ MinerU
   ├─ LangExtract
   └─ PyMuPDF
```

---

## 23. 总结

FusionMark 前端建议从当前原生结构升级为：

```txt
Vue 3 + Vite + TypeScript + Naive UI + Pinia + Vue Router + Axios + PDF.js
```

核心改造原则：

- 页面负责布局
- 组件负责展示
- Store 负责状态
- API 层负责请求
- Composables 负责复杂业务逻辑
- 环境变量负责开发 / 生产差异
- Naive UI 负责基础交互组件
- 自定义 CSS 变量保留 FusionMark 的品牌风格

这样改造后，项目会从“可运行的前端 Demo”升级为“可长期维护、可扩展、可部署”的生产级前端工程。
