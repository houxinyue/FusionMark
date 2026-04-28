<template>
  <div class="url-card">
    <label class="url-label">文档 URL</label>
    <div class="url-input-group">
      <n-input
        v-model:value="url"
        class="url-input"
        placeholder="粘贴文件链接地址..."
        :disabled="isProcessing"
      />
      <n-button type="primary" :loading="isProcessing" @click="handleSubmit">
        开始
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NInput, NButton } from 'naive-ui'
import { useTaskStore } from '@/stores/taskStore'

const url = ref('')
const taskStore = useTaskStore()
const isProcessing = computed(() => taskStore.isProcessing)

function handleSubmit() {
  if (!url.value.trim()) {
    console.warn('请输入文件链接')
    return
  }
  console.log('Submit URL:', url.value)
}
</script>

<style scoped>
.url-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-sunken);
}

.url-label {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  font-weight: 700;
}

.url-input-group {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

.url-input {
  flex: 1;
  --n-color: #ffffff;
  --n-color-focus: #ffffff;
  --n-border: 1px solid var(--border-subtle);
  --n-border-hover: 1px solid rgba(251, 146, 60, 0.48);
  --n-border-focus: 1px solid rgba(249, 115, 22, 0.78);
  --n-box-shadow-focus: 0 0 0 3px rgba(249, 115, 22, 0.14);
}

.url-input :deep(.n-input__input-el) {
  color: var(--text-primary);
  font-size: var(--font-body);
}
</style>
