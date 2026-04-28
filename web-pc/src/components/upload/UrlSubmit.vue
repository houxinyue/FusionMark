<template>
  <div class="url-card">
    <label class="url-label">文档 URL</label>
    <div class="url-input-group">
      <n-input
        v-model:value="url"
        class="url-input"
        placeholder="粘贴文件链接地址..."
        :disabled="isProcessing"
        @keyup.enter="handleSubmit"
      />
      <n-button type="primary" :loading="isProcessing" @click="handleSubmit">
        开始
      </n-button>
    </div>
    <p v-if="feedback" class="url-feedback" :class="{ error: hasError }">{{ feedback }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NInput, NButton } from 'naive-ui'
import { createTask } from '@/api/taskApi'
import { useTaskWebSocket } from '@/composables/useTaskWebSocket'
import { useTaskStore } from '@/stores/taskStore'

const url = ref('')
const feedback = ref('')
const hasError = ref(false)
const taskStore = useTaskStore()
const { connect } = useTaskWebSocket()
const isProcessing = computed(() => taskStore.isProcessing)

function setFeedback(message: string, error = false) {
  feedback.value = message
  hasError.value = error
}

async function handleSubmit() {
  const documentUrl = url.value.trim()
  if (!documentUrl) {
    setFeedback('请输入文件链接', true)
    return
  }

  if (!/^https?:\/\//i.test(documentUrl)) {
    setFeedback('链接必须以 http:// 或 https:// 开头', true)
    return
  }

  setFeedback('正在提交任务...')

  try {
    const response = await createTask({
      document_url: documentUrl,
      model: 'vlm',
      enable_ocr: true,
      enable_formula: true,
      enable_table: true,
      language: 'ch',
    })

    taskStore.startTask(response.task_id)
    taskStore.applyTaskSnapshot(response)
    connect(response.task_id)
    setFeedback('任务已提交，正在接收实时进度')
  } catch (e) {
    console.error('Submit URL failed:', e)
    taskStore.failTask('任务提交失败')
    setFeedback('任务提交失败，请检查后端服务和文档链接', true)
  }
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

.url-feedback {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--font-caption);
  line-height: 1.5;
}

.url-feedback.error {
  color: var(--state-danger);
}
</style>
