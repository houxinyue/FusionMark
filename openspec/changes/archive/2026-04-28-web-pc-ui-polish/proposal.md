# Web-PC UI 视觉优化与交互增强

## Problem / Intent

当前 `web-pc/` 前端工程已完成基础脚手架搭建，但 UI 视觉层面存在以下不足：

1. **缺少骨架屏（Skeleton）状态**：任务提交后、PDF 加载前等过渡阶段无加载反馈，用户面对空白区域产生焦虑感
2. **左侧面板 380px 固定宽度过于刚性**：在 1280px 以下屏幕或分屏开发场景会挤压右侧 PDF 预览区域
3. **空状态行星动画与业务关联度弱**：轨道旋转动画好看但与「PDF 智能解析」主题无关，且多组旋转动画叠加消耗性能
4. **进度条 shimmer 高光刺眼**：`rgba(255,255,255,0.3)` 的白色光条在深色背景上对比度过高，视觉上像「故障」而非「流动」
5. **实体标签缺少交互反馈**：静态标签没有 hover 和点击态，用户无法感知是否可交互
6. **缺少字体层级系统**：各组件字号未统一规范，容易导致视觉层次混乱

## Scope

对 `web-pc/src/` 进行以下视觉优化：

1. **新增骨架屏组件与样式**：定义统一的 skeleton 动画规范，覆盖进度卡片、PDF 预览区、历史列表
2. **新增响应式断点**：为 ProcessPdfView 左侧面板增加 `@media` 断点（1280px / 1024px）
3. **空状态动画替换**：将行星轨道替换为「文档扫描流」动画，更贴合 PDF 解析业务
4. **进度条 shimmer 柔化**：将白色高光改为克莱因蓝微光，降低亮度并增加 blur 柔化
5. **实体标签交互增强**：增加 hover 上浮、阴影、类别指示圆点
6. **字体层级系统**：在 CSS 变量中定义 `--font-display` 到 `--font-tiny` 的完整阶梯

## Out of Scope

- 不修改任何业务逻辑（API 调用、WebSocket、PDF 渲染）
- 不新增页面或路由
- 不改动 Naive UI 主题覆盖的基础配置
- 不涉及移动端适配（仅优化 PC 端响应式）

## Affected Modules

- `web-pc/src/styles/variables.css` — 新增字体层级变量
- `web-pc/src/styles/animations.css` — 新增骨架屏、文档扫描动画
- `web-pc/src/components/` — 多组件样式优化
  - `upload/PdfUpload.vue` — 骨架屏状态
  - `progress/ProgressCard.vue` — 骨架屏 + shimmer 柔化
  - `progress/StageList.vue` — 字体层级对齐
  - `pdf/PdfViewer.vue` — 空状态动画替换 + 骨架屏
  - `entity/EntityModal.vue` — 标签 hover 交互
- `web-pc/src/views/ProcessPdfView.vue` — 响应式断点

## Architecture / Design Approach

### 骨架屏设计

采用「流光扫过」效果，使用 CSS `linear-gradient` + `background-position` 动画：

```css
.skeleton {
  background: linear-gradient(90deg, var(--bg-secondary) 25%, rgba(255,255,255,0.03) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: skeletonShimmer 1.5s infinite;
}
```

### 响应式策略

| 断点 | 行为 |
|---|---|
| `>1280px` | 默认双栏，左侧面板 380px |
| `1024px-1280px` | 左侧面板收窄至 320px |
| `<1024px` | 单栏垂直堆叠，左侧 max-height: 50vh |

### 空状态动画

使用 `clip-path` + `filter brightness` 模拟文档扫描过程，比行星轨道更贴合业务：

```css
@keyframes docScan {
  0% { clip-path: inset(0 100% 0 0); opacity: 0; }
  30% { clip-path: inset(0 0 0 0); opacity: 1; }
  100% { filter: brightness(1.1); }
}
```

## Data or API Contract Changes

无。

## Risks

| 风险 | 缓解措施 |
|---|---|
| 响应式断点改变现有布局习惯 | 保留默认桌面端布局不变，仅在小屏幕触发 |
| 空状态动画替换用户已习惯 | 新动画更贴合业务，且仅影响未上传文件时的空状态 |
| skeleton 动画增加性能开销 | 使用纯 CSS 动画，GPU 加速，避免 JS 计算 |

## Validation Plan

1. `pnpm build` 生产构建成功，无新增类型/语法错误
2. 在 1920px / 1366px / 1024px 三种分辨率下检查布局正常
3. 骨架屏在「提交 URL 后、WebSocket 首次返回前」正确显示
4. 进度条 shimmer 动画视觉上柔和、不刺眼
5. 实体标签 hover 有明确的上浮 + 阴影反馈

## Rollback Plan

所有改动均为 CSS/样式层，不涉及业务逻辑。如需要回退，可逐个文件恢复原始版本，或直接撤销本次 commit。
