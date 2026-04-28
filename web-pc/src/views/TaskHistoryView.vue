<template>
  <div class="tool-page">
    <section class="tool-shell">
      <div class="page-header">
        <p class="eyebrow">History</p>
        <h2>任务历史</h2>
        <p>近期解析任务、处理状态与产物入口将在这里集中展示。</p>
      </div>
      <div class="table-shell">
        <div class="table-row table-head">
          <span>任务</span>
          <span>状态</span>
          <span>更新时间</span>
        </div>
        <div class="empty-row">暂无任务记录</div>
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
  max-width: 720px;
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

.table-shell {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-sunken);
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 160px 180px;
  gap: 12px;
  padding: 10px 12px;
}

.table-head {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  font-weight: 800;
  background: rgba(241, 245, 249, 0.74);
  border-bottom: 1px solid var(--border-subtle);
}

.empty-row {
  padding: 40px 12px;
  color: var(--text-subtle);
  font-size: var(--font-body);
  text-align: center;
}
</style>
