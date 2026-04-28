<template>
  <div class="progress-card" v-if="taskStore.isProcessing || taskStore.progress">
    <div v-if="showSkeleton" class="skeleton-state">
      <div class="skeleton skeleton-block" style="width: 40%; height: 18px; margin-bottom: 12px;" />
      <div class="skeleton skeleton-block" style="width: 100%; height: 8px; margin-bottom: 16px; border-radius: 4px;" />
      <div class="skeleton skeleton-block" style="width: 80%; height: 14px; margin-bottom: 8px;" />
      <div class="skeleton skeleton-block" style="width: 60%; height: 14px; margin-bottom: 8px;" />
      <div class="skeleton skeleton-block" style="width: 70%; height: 14px;" />
    </div>

    <template v-else>
      <div class="progress-header">
        <span class="progress-title">处理状态</span>
        <span class="progress-percent">{{ overallProgress }}%</span>
      </div>
      <div class="progress-summary">
        <span class="status-badge" :class="statusClass">{{ statusLabel }}</span>
        <span class="current-stage">{{ currentStageText }}</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: overallProgress + '%' }" />
        <div v-if="overallProgress > 0 && overallProgress < 100" class="progress-glow" />
      </div>
      <StageList />
      <ProgressLogs />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTaskStore } from '@/stores/taskStore'
import { STAGE_LABELS } from '@/constants/stage'
import StageList from './StageList.vue'
import ProgressLogs from './ProgressLogs.vue'

const taskStore = useTaskStore()

const overallProgress = computed(() => {
  return taskStore.progress?.overall_progress ?? 0
})

const showSkeleton = computed(() => {
  return taskStore.isProcessing && taskStore.progress === null
})

const statusClass = computed(() => {
  const state = taskStore.status
  if (state === 'completed') return 'completed'
  if (state === 'failed') return 'failed'
  if (taskStore.isProcessing) return 'processing'
  return 'pending'
})

const statusLabel = computed(() => {
  const state = taskStore.status
  if (state === 'completed') return '已完成'
  if (state === 'failed') return '失败'
  if (taskStore.isProcessing) return '处理中'
  return '待处理'
})

const currentStageText = computed(() => {
  const stages = taskStore.progress
  if (!stages) return '等待任务开始'
  for (const key of ['mineru', 'extraction', 'highlight'] as const) {
    const s = stages[key]
    if (s && s.state === 'running') {
      return STAGE_LABELS[key] ?? key
    }
  }
  return '等待任务开始'
})
</script>

<style scoped>
.progress-card {
  background: var(--surface-sunken);
  border-radius: var(--radius-lg);
  padding: 14px;
  border: 1px solid var(--border-subtle);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-title {
  font-size: var(--font-body);
  font-weight: 700;
  color: var(--text-primary);
}

.progress-percent {
  font-size: var(--font-body);
  font-weight: 800;
  color: var(--brand-orange-soft);
}

.progress-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: 12px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 66px;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-tiny);
  font-weight: 800;
}

.status-badge.pending {
  background: rgba(148, 163, 184, 0.12);
  color: var(--state-pending);
}

.status-badge.processing {
  background: rgba(249, 115, 22, 0.14);
  color: var(--brand-orange-soft);
}

.status-badge.completed {
  background: rgba(34, 197, 94, 0.14);
  color: var(--state-success);
}

.status-badge.failed {
  background: rgba(244, 63, 94, 0.14);
  color: var(--state-danger);
}

.current-stage {
  font-size: var(--font-caption);
  color: var(--text-muted);
  text-align: right;
}

.progress-bar {
  height: 6px;
  background: rgba(226, 232, 240, 0.82);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
  margin-bottom: 14px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--brand-orange-deep), var(--brand-orange), var(--brand-orange-soft));
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
  position: relative;
  box-shadow: var(--glow-scan);
}

.progress-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 56px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(251, 146, 60, 0.24), transparent);
  filter: blur(3px);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-56px); }
  100% { transform: translateX(56px); }
}

.skeleton-state {
  padding: 4px 0;
}
</style>
