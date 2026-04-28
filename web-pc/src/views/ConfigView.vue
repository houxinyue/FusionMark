<template>
  <div class="tool-page">
    <section class="tool-shell">
      <div class="page-header">
        <p class="eyebrow">Profiles</p>
        <h2>配置管理</h2>
        <p>解析提示词、实体类别颜色、模型参数与 few-shot 示例将在这里统一维护。</p>
      </div>
      <div class="config-grid">
        <div class="config-card">
          <span class="card-kicker">Active</span>
          <strong>默认高亮配置</strong>
          <p>当前配置摘要占位</p>
        </div>
        <div class="config-card">
          <span class="card-kicker">Schema</span>
          <strong>实体类别</strong>
          <p>类别颜色与抽取字段占位</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.tool-page {
  flex: 1;
  padding: 12px;
  overflow: auto;
}

.tool-shell {
  min-height: 360px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-rail);
  box-shadow: var(--shadow-sm);
}

.page-header {
  max-width: 760px;
  margin-bottom: 18px;
}

.eyebrow {
  margin-bottom: 4px;
  color: var(--brand-orange-soft);
  font-size: var(--font-tiny);
  font-weight: 800;
  text-transform: uppercase;
}

h2 {
  margin-bottom: 8px;
  color: var(--text-primary);
  font-size: var(--font-display);
}

p {
  color: var(--text-muted);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 12px;
}

.config-card {
  min-height: 120px;
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-sunken);
}

.card-kicker {
  display: block;
  margin-bottom: 8px;
  color: var(--brand-orange-soft);
  font-size: var(--font-tiny);
  font-weight: 800;
  text-transform: uppercase;
}

.config-card strong {
  display: block;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.config-card p {
  font-size: var(--font-caption);
}

@media (max-width: 760px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
}
</style>
