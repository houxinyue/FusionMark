<template>
  <header class="header">
    <RouterLink to="/" class="logo" aria-label="FusionMark">
      <img src="@/assets/images/fusion_mark_logo.svg" alt="" class="logo-img" />
      <span class="logo-text">FusionMark</span>
    </RouterLink>
    <nav class="nav">
      <RouterLink to="/" class="nav-link" active-class="active">处理 PDF</RouterLink>
      <RouterLink to="/history" class="nav-link" active-class="active">任务历史</RouterLink>
      <RouterLink to="/config" class="nav-link" active-class="active">配置</RouterLink>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 62px;
  padding: 0 20px;
  background: rgba(255, 255, 255, 0.88);
  border-bottom: 1px solid var(--border-subtle);
  backdrop-filter: var(--backdrop-panel);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.logo {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: var(--text-primary);
  text-decoration: none;
}

.logo-img {
  width: 42px;
  height: 42px;
  object-fit: contain;
  filter: drop-shadow(0 4px 10px rgba(249, 115, 22, 0.22));
}

.logo-text {
  font-size: 20px;
  font-weight: 750;
  letter-spacing: 0;
  color: var(--text-primary);
}

.nav {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(248, 250, 252, 0.78);
}

.nav-link {
  position: relative;
  padding: 6px 12px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: var(--font-caption);
  font-weight: 600;
  border-radius: var(--radius-md);
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast);
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--surface-hover);
}

.nav-link.active {
  color: var(--text-primary);
  background: rgba(249, 115, 22, 0.12);
}

@media (max-width: 640px) {
  .header {
    padding: 0 12px;
  }

  .logo-text {
    display: none;
  }

  .nav-link {
    padding: 6px 8px;
  }
}
</style>
