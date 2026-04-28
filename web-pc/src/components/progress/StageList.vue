<template>
  <div class="stage-list">
    <div
      v-for="stage in stages"
      :key="stage.key"
      class="stage-item"
      :class="[stage.state, stage.key]"
    >
      <div class="stage-main">
        <span class="stage-name">{{ stage.name }}</span>
        <span class="stage-state">{{ stateLabel(stage.state) }}</span>
      </div>
      <span class="stage-progress">{{ stage.progress }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTaskStore } from '@/stores/taskStore'
import { STAGE_DISPLAY_NAMES } from '@/constants/stage'

const taskStore = useTaskStore()

const stages = computed(() => {
  const order = ['mineru', 'extraction', 'highlight'] as const
  return order.map((key) => {
    const data = taskStore.progress?.[key] ?? { state: 'pending', progress: 0 }
    return {
      key,
      name: STAGE_DISPLAY_NAMES[key] ?? key,
      state: data.state,
      progress: data.progress,
    }
  })
})

function stateLabel(state: string) {
  const labels: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    running: '处理中',
    completed: '已完成',
    done: '已完成',
    failed: '失败',
  }
  return labels[state] ?? state
}
</script>

<style scoped>
.stage-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.stage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 10px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition:
    border-color var(--transition-fast),
    background-color var(--transition-fast);
}

.stage-item.processing,
.stage-item.running {
  border-color: rgba(251, 146, 60, 0.46);
  background: rgba(249, 115, 22, 0.08);
}

.stage-item.completed,
.stage-item.done {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.06);
}

.stage-item.failed {
  border-color: rgba(244, 63, 94, 0.36);
  background: rgba(244, 63, 94, 0.07);
}

.stage-main {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stage-name {
  font-size: var(--font-caption);
  font-weight: 700;
  color: var(--text-primary);
}

.stage-state {
  font-size: var(--font-tiny);
  color: var(--text-subtle);
}

.stage-progress {
  font-size: var(--font-caption);
  font-weight: 800;
  color: var(--text-secondary);
}

.stage-item.processing .stage-state,
.stage-item.processing .stage-progress,
.stage-item.running .stage-state,
.stage-item.running .stage-progress {
  color: var(--brand-orange-soft);
}

.stage-item.completed .stage-state,
.stage-item.completed .stage-progress,
.stage-item.done .stage-state,
.stage-item.done .stage-progress {
  color: var(--state-success);
}

.stage-item.failed .stage-state,
.stage-item.failed .stage-progress {
  color: var(--state-danger);
}
</style>
