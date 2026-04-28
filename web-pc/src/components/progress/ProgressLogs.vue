<template>
  <div class="progress-logs">
    <div class="logs-header">实时日志</div>
    <div class="log-list">
      <div v-if="taskStore.logs.length === 0" class="log-empty">等待任务日志...</div>
      <div v-for="(log, index) in taskStore.logs" :key="index" class="log-item">
        {{ log }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTaskStore } from '@/stores/taskStore'

const taskStore = useTaskStore()
</script>

<style scoped>
.progress-logs {
  margin-top: 10px;
}

.logs-header {
  font-size: var(--font-caption);
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.log-list {
  max-height: 180px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 8px;
}

.log-empty {
  font-size: var(--font-caption);
  color: var(--text-subtle);
  text-align: center;
  padding: 14px 0;
}

.log-item {
  font-size: var(--font-caption);
  color: var(--text-secondary);
  padding: 2px 0;
  font-family: Consolas, 'Courier New', monospace;
}
</style>
