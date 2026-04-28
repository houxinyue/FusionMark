# Tasks

## 1. Design
- [x] 确认 6 项优化方向（骨架屏、响应式、空状态、shimmer、标签交互、字体层级）
- [x] 确认影响文件范围
- [x] 撰写 OpenSpec proposal.md
- [x] 撰写 OpenSpec tasks.md
- [x] 撰写 OpenSpec spec.md（delta requirements）
- [x] 运行 openspec validate 通过验证
- [x] 等待用户批准提案

## 2. Implementation
- [x] 更新 `src/styles/variables.css` — 新增字体层级变量
- [x] 新建 `src/styles/animations.css` — 新增 skeletonShimmer、docScan 等动画
- [x] 更新 `src/components/progress/ProgressCard.vue` — shimmer 柔化 + 骨架屏状态
- [x] 更新 `src/components/pdf/PdfViewer.vue` — 空状态动画替换为文档扫描 + 骨架屏
- [x] 更新 `src/components/upload/PdfUpload.vue` — 骨架屏状态
- [x] 更新 `src/views/ProcessPdfView.vue` — 响应式断点（1280px / 1024px）
- [x] 更新 `src/components/entity/EntityModal.vue` — 实体标签 hover 交互
- [x] 更新 `src/components/progress/StageList.vue` — 字体层级对齐
- [x] 更新 `src/styles/main.css` — 引入 animations.css

## 3. Validation
- [x] `pnpm build` 构建成功
- [ ] 多分辨率布局检查（1920 / 1366 / 1024）
- [ ] 骨架屏显示时机验证
- [ ] 进度条 shimmer 视觉柔和度确认
- [ ] 实体标签 hover 反馈确认
