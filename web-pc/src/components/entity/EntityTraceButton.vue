<template>
  <div class="entities-preview">
    <h3 class="section-title">文本实体回溯</h3>
    <n-button
      class="btn-entity-trace"
      type="primary"
      ghost
      :disabled="disabled"
      :loading="loading"
      block
      @click="emit('click')"
    >
      查看提取结果
    </n-button>
    <p class="entity-trace-hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'

defineProps<{
  disabled?: boolean
  loading?: boolean
  hint?: string
}>()

const emit = defineEmits<{
  click: []
}>()
</script>

<style scoped>
.entities-preview {
  background: var(--surface-sunken);
  border-radius: var(--radius-lg);
  padding: 14px;
  border: 1px solid var(--border-subtle);
}

.section-title {
  font-size: var(--font-body);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title::before {
  content: '';
  width: 3px;
  height: 16px;
  background: var(--brand-orange);
  border-radius: var(--radius-full);
}

.btn-entity-trace {
  width: 100%;
  justify-content: center;
}

.entity-trace-hint {
  margin: 8px 0 0;
  font-size: var(--font-caption);
  color: var(--text-subtle);
  line-height: 1.5;
  text-align: center;
}
</style>
