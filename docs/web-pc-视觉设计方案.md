# FusionMark Web-PC 视觉设计方案

> 基于现有 `frontend/` 代码分析，为 `web-pc/` Vue 3 工程提供的完整视觉与交互设计迁移方案。

---

## 一、色彩体系迁移

现有前端已建立非常完整的深色科技风配色，迁移到 `web-pc` 时需完整保留。

### 1.1 CSS 变量映射（`src/styles/variables.css`）

```css
:root {
  /* ===== 核心品牌色 ===== */
  --klein-blue: #002FA7;
  --klein-blue-light: #1a4fc7;
  --klein-blue-dark: #001f7a;
  --klein-blue-glow: rgba(0, 47, 167, 0.4);

  --hermes-orange: #FF6600;
  --hermes-orange-light: #ff8533;
  --hermes-orange-glow: rgba(255, 102, 0, 0.4);

  /* ===== 莫兰迪实体高亮色 ===== */
  --morandi-beige: #E8D5C4;      /* 公司名 / 报告标题 */
  --morandi-gray-blue: #B8C5D6;  /* 数值 / 份额 */
  --morandi-mint: #A8D5BA;       /* 正增长 */
  --morandi-rose: #E8B4B4;       /* 负增长 */
  --morandi-lavender: #C9B8D6;   /* 其他 */

  /* ===== 背景层级 ===== */
  --bg-primary: #1A1A2E;         /* 页面底色 */
  --bg-secondary: #16213E;       /* Header / Footer / 工具栏 */
  --bg-tertiary: #0F3460;        /* 进度条轨道 / 输入框背景 */
  --bg-card: rgba(255, 255, 255, 0.03);  /* 卡片底色 */
  --bg-hover: rgba(255, 255, 255, 0.05); /* hover 态 */
  --bg-backdrop: rgba(15, 23, 42, 0.48); /* 弹窗遮罩 */

  /* ===== 文字色 ===== */
  --text-primary: #FFFFFF;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-muted: rgba(255, 255, 255, 0.5);

  /* ===== 状态色 ===== */
  --status-success: #15803d;
  --status-success-bg: rgba(22, 163, 74, 0.14);
  --status-error: #dc2626;
  --status-error-bg: rgba(220, 38, 38, 0.14);
  --status-pending-bg: rgba(107, 114, 128, 0.14);

  /* ===== 边框与分割 ===== */
  --border-color: rgba(255, 255, 255, 0.1);
  --border-focus: var(--klein-blue);
  --border-active: rgba(0, 47, 167, 0.35);

  /* ===== 阴影 ===== */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.3);
  --shadow-glow: 0 0 20px var(--klein-blue-glow);
  --shadow-orange-glow: 0 0 20px var(--hermes-orange-glow);
  --shadow-modal: 0 24px 80px rgba(15, 23, 42, 0.28);

  /* ===== 间距 ===== */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* ===== 圆角 ===== */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* ===== 过渡 ===== */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
}
```

### 1.2 Naive UI 主题覆盖（`App.vue`）

```ts
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#002FA7',
    primaryColorHover: '#1a4fc7',
    primaryColorPressed: '#001f7a',
    primaryColorSuppl: '#1a4fc7',
    warningColor: '#FF6600',
    warningColorHover: '#ff8533',
    bodyColor: '#1A1A2E',
    cardColor: 'rgba(255, 255, 255, 0.03)',
    modalColor: '#16213E',
    tableColor: 'transparent',
    borderRadius: '12px',
    borderRadiusSmall: '6px',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  Button: {
    colorPrimary: '#002FA7',
    colorPrimaryHover: '#1a4fc7',
    colorPrimaryPressed: '#001f7a',
    colorWarning: '#FF6600',
    colorWarningHover: '#ff8533',
  },
  Input: {
    color: '#16213E',
    colorFocus: '#16213E',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderFocus: '#002FA7',
    boxShadowFocus: '0 0 0 3px rgba(0, 47, 167, 0.2)',
    placeholderColor: 'rgba(255, 255, 255, 0.5)',
    textColor: '#FFFFFF',
  },
  Progress: {
    railColor: '#0F3460',
    fillColor: '#002FA7',
  },
  Card: {
    color: 'rgba(255, 255, 255, 0.03)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
}
```

---

## 二、动画系统迁移

现有 `main.css` 中定义了 6 组核心动画，需在 `web-pc` 中完整保留。

### 2.1 动画清单（`src/styles/animations.css`）

```css
/* ===== 进度条光条扫过 ===== */
@keyframes shimmer {
  0% { transform: translateX(-60px); }
  100% { transform: translateX(60px); }
}

/* ===== 实体标签弹出 ===== */
@keyframes tagIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* ===== 空状态行星轨道 ===== */
@keyframes orbit {
  from {
    transform: rotate(0deg) translateX(60px) rotate(0deg);
  }
  to {
    transform: rotate(360deg) translateX(60px) rotate(-360deg);
  }
}

/* ===== 通知滑入 ===== */
@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* ===== 通知滑出 ===== */
@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

/* ===== 淡入上浮（通用进入动画） ===== */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== 脉冲呼吸（处理中状态） ===== */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
```

### 2.2 Vue 过渡组件封装建议

```vue
<!-- components/transition/FadeTransition.vue -->
<template>
  <Transition name="fade-up">
    <slot />
  </Transition>
</template>

<style>
.fade-up-enter-active {
  transition: all 0.3s ease;
}
.fade-up-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
</style>
```

---

## 三、关键组件视觉设计

### 3.1 Logo（`AppHeader.vue`）

保留现有渐变文字效果：

```vue
<span class="logo-text">FusionMark</span>

<style scoped>
.logo-icon {
  font-size: 24px;
  color: var(--klein-blue);
  text-shadow: 0 0 10px rgba(0, 47, 167, 0.5);
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--klein-blue-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
```

### 3.2 上传区域（`PdfUpload.vue`）

保留悬浮渐变扫光 + 拖拽态变色：

```css
.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-xl);
  text-align: center;
  transition: all var(--transition-normal);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

/* 悬浮时的渐变光晕 */
.upload-area::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(0, 47, 167, 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.upload-area:hover {
  border-color: var(--klein-blue);
  background: var(--bg-hover);
}

.upload-area:hover::before {
  opacity: 1;
}

/* 拖拽态变为爱马仕橙 */
.upload-area.dragover {
  border-color: var(--hermes-orange);
  background: rgba(255, 102, 0, 0.05);
}
```

### 3.3 进度条（`ProgressCard.vue`）

保留渐变填充 + shimmer 光条：

```css
.progress-bar {
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--klein-blue) 0%, var(--klein-blue-light) 100%);
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
  position: relative;
}

/* 光条扫过动画 */
.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 60px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 2s infinite;
}
```

### 3.4 阶段列表（`StageList.vue`）

保留三种状态边框色：

```css
.stage-item {
  padding: 10px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: border-color var(--transition-fast), background-color var(--transition-fast);
}

/* 进行中 - 克莱因蓝边框 */
.stage-item.active {
  border-color: rgba(0, 47, 167, 0.35);
  background: rgba(0, 47, 167, 0.06);
}

/* 已完成 - 绿色边框 */
.stage-item.completed {
  border-color: rgba(22, 163, 74, 0.3);
  background: rgba(22, 163, 74, 0.06);
}

/* 失败 - 红色边框 */
.stage-item.failed {
  border-color: rgba(220, 38, 38, 0.3);
  background: rgba(220, 38, 38, 0.06);
}
```

### 3.5 空状态动画（`PdfViewer.vue` 空状态）

保留行星轨道旋转：

```css
.orbit {
  width: 200px;
  height: 200px;
  position: relative;
  animation: rotate 20s linear infinite;
}

.planet {
  width: 60px;
  height: 60px;
  background: radial-gradient(circle at 30% 30%, var(--klein-blue-light), var(--klein-blue));
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  box-shadow:
    0 0 40px rgba(0, 47, 167, 0.4),
    inset -10px -10px 20px rgba(0, 0, 0, 0.3);
}

.satellite.s1 {
  width: 20px;
  height: 20px;
  background: var(--hermes-orange);
  top: 20%;
  left: 20%;
  box-shadow: 0 0 15px rgba(255, 102, 0, 0.5);
  animation: orbit 10s linear infinite reverse;
}

.satellite.s2 {
  width: 12px;
  height: 12px;
  background: var(--morandi-mint);
  bottom: 25%;
  right: 20%;
  animation: orbit 15s linear infinite;
}
```

### 3.6 实体标签（`EntityModal.vue`）

保留莫兰迪色 + 弹出动画：

```css
.entity-tag {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  animation: tagIn 0.3s ease;
}

.entity-tag.company {
  background: var(--morandi-beige);
  color: #5a4a3a;
}

.entity-tag.value {
  background: var(--morandi-gray-blue);
  color: #3a4a5a;
}

.entity-tag.positive {
  background: var(--morandi-mint);
  color: #2a5a3a;
}

.entity-tag.negative {
  background: var(--morandi-rose);
  color: #5a3a3a;
}
```

### 3.7 预览区背景（`ProcessPdfView.vue` 右侧面板）

保留径向渐变装饰：

```css
.preview-container {
  background:
    radial-gradient(circle at 20% 80%, rgba(0, 47, 167, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 102, 0, 0.03) 0%, transparent 50%),
    var(--bg-primary);
}
```

---

## 四、按钮与交互规范

| 类型 | 背景 | Hover 效果 | 用途 |
|---|---|---|---|
| **Primary** | `#002FA7` | `background: #1a4fc7` + `box-shadow: 0 0 20px rgba(0,47,167,0.4)` + `translateY(-1px)` | 主操作（开始处理） |
| **Secondary** | `#0F3460` | `background: rgba(255,255,255,0.05)` + `border-color: #002FA7` | 次级操作（选择文件） |
| **Download** | `#FF6600` | `background: #ff8533` + `box-shadow: 0 0 20px rgba(255,102,0,0.4)` | 下载结果 |
| **Tool Button** | transparent | `background: rgba(255,255,255,0.05)` + `color: #fff` | 工具栏按钮 |
| **Active** | `#002FA7` | - | 当前激活态 |

---

## 五、全局样式细节

### 5.1 自定义滚动条

```css
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--klein-blue);
}
```

### 5.2 通知消息（`useNotification.ts` 需实现）

```css
.notification {
  position: fixed;
  top: 80px;
  right: 20px;
  padding: 12px 20px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

/* 四种状态色 */
.notification.info { background: var(--klein-blue); color: white; }
.notification.success { background: var(--morandi-mint); color: #333; }
.notification.warning { background: var(--morandi-beige); color: #333; }
.notification.error { background: var(--morandi-rose); color: #333; }
```

### 5.3 Section Title 装饰线

```css
.section-title {
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.section-title::before {
  content: '';
  width: 4px;
  height: 16px;
  background: var(--hermes-orange);
  border-radius: var(--radius-full);
}
```

---

## 六、布局结构保留

现有布局为三行结构，迁移到 Vue 后保持：

```
+------------------------------------------------------------------+
| Header (64px, sticky)                                            |
|  Logo                                    Nav                     |
+------------------------------------------------------------------+
| Main (flex: 1)                                                   |
|  +-------------------+  +-------------------------------------+  |
|  | Left Panel        |  | Right Panel                         |  |
|  | (380px 固定)       |  | (flex: 1)                           |  |
|  |                   |  |                                     |  |
|  +-------------------+  +-------------------------------------+  |
+------------------------------------------------------------------+
| Footer (48px)                                                    |
+------------------------------------------------------------------+
```

---

## 七、迁移实施建议

1. **第一步**：将上述 CSS 变量完整写入 `src/styles/variables.css`，替换现有简陋版本
2. **第二步**：新建 `src/styles/animations.css` 存放所有 keyframes
3. **第三步**：更新 `App.vue` 的 `themeOverrides`，确保 Naive UI 组件与自定义变量一致
4. **第四步**：各组件逐步从 `frontend/main.css` 中抽取对应样式，转为 `<style scoped>`
5. **第五步**：`useNotification.ts` 接入 Naive UI `n-message` 或自建 DOM 通知，实现 `slideIn`/`slideOut` 动画

> **原则**：所有颜色值必须与现有 `frontend/main.css` 完全一致，确保新旧前端视觉统一。动画时序和曲线也保持不变，用户在迁移后不应感受到视觉差异。
