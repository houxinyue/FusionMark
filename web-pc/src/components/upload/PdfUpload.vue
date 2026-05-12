<template>
  <div class="upload-wrapper">
    <div
      class="upload-area"
      :class="{ 'upload-loading': loading }"
      @click="handleClick"
      @dragover.prevent
      @drop.prevent="handleDrop"
    >
      <div v-if="loading" class="upload-skeleton">
        <div class="skeleton skeleton-block upload-skeleton-icon" />
        <div class="skeleton skeleton-block upload-skeleton-text" />
        <div class="skeleton skeleton-block upload-skeleton-hint" />
      </div>

      <div v-else class="upload-content">
        <div class="upload-icon" aria-hidden="true">
          <span></span>
        </div>
        <p class="upload-text">拖放文件到此</p>
        <p class="upload-hint">支持 PDF、MD、图片、PPT 文件</p>
        <n-button class="upload-btn" type="primary" size="small">选择文件</n-button>
        <p v-if="feedback" class="upload-feedback" :class="{ error: hasError }">{{ feedback }}</p>
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg,.html,.htm"
          hidden
          @change="handleFileChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NButton } from 'naive-ui'
import { uploadTask } from '@/api/taskApi'
import { useTaskWebSocket } from '@/composables/useTaskWebSocket'
import { useTaskStore } from '@/stores/taskStore'

const props = defineProps<{
  loading?: boolean
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const feedback = ref('')
const hasError = ref(false)
const taskStore = useTaskStore()
const { connect } = useTaskWebSocket()
const isProcessing = computed(() => Boolean(props.loading) || taskStore.isProcessing)

function handleClick() {
  if (!isProcessing.value && fileInput.value) {
    fileInput.value.click()
  }
}

function setFeedback(message: string, error = false) {
  feedback.value = message
  hasError.value = error
}

function extractApiError(error: unknown) {
  const response = (error as { response?: { status?: number; data?: { detail?: unknown } } })?.response
  const detail = response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return response?.status ? `${response.status}: ${detail}` : detail
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return '未知错误'
}

async function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (file) {
    await submitFile(file)
  }
}

async function handleDrop(e: DragEvent) {
  if (isProcessing.value) return
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    await submitFile(files[0])
  }
}

async function submitFile(file: File) {
  const supported = /\.(pdf|docx?|pptx?|png|jpe?g|html?|htm)$/i
  if (!supported.test(file.name)) {
    setFeedback('暂不支持该文件类型，请上传 PDF、Word、PPT、图片或 HTML 文件', true)
    return
  }

  setFeedback('正在上传并提交任务...')

  try {
    const response = await uploadTask({
      file,
      model: 'vlm',
      enable_ocr: true,
      enable_formula: true,
      enable_table: true,
      language: 'ch',
    })

    taskStore.startTask(response.task_id)
    taskStore.applyTaskSnapshot(response)
    connect(response.task_id)
    setFeedback('文件已上传，正在接收实时进度')
  } catch (error) {
    console.error('Upload task failed:', error)
    const message = extractApiError(error)
    taskStore.failTask(`上传任务提交失败：${message}`)
    setFeedback(`上传任务提交失败：${message}`, true)
  }
}
</script>

<style scoped>
.upload-wrapper {
  width: 100%;
}

.upload-area {
  border: 1px dashed rgba(251, 146, 60, 0.44);
  border-radius: var(--radius-lg);
  padding: 18px 14px;
  text-align: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition:
    border-color var(--transition-normal),
    background-color var(--transition-normal),
    box-shadow var(--transition-normal);
  background:
    linear-gradient(180deg, rgba(249, 115, 22, 0.045), rgba(255, 255, 255, 0.72)),
    var(--surface-sunken);
}

.upload-area:hover {
  border-color: var(--brand-orange-soft);
  box-shadow:
    inset 0 0 28px rgba(249, 115, 22, 0.08),
    0 0 18px rgba(249, 115, 22, 0.12);
}


.upload-area.upload-loading {
  cursor: not-allowed;
  border-color: var(--border-color);
}

.upload-content {
  position: relative;
  z-index: 1;
}

.upload-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 54px;
  margin-bottom: 12px;
  border: 1px solid rgba(248, 250, 252, 0.22);
  border-radius: var(--radius-md);
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(255, 237, 213, 0.56));
  box-shadow: inset 0 -10px 22px rgba(249, 115, 22, 0.08);
}

.upload-icon span {
  width: 24px;
  height: 2px;
  background: var(--brand-orange-soft);
  box-shadow:
    0 8px 0 rgba(251, 146, 60, 0.72),
    0 -8px 0 rgba(251, 146, 60, 0.42);
}

.upload-text {
  font-size: var(--font-body);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.upload-hint {
  font-size: var(--font-caption);
  color: var(--text-muted);
  margin-bottom: 12px;
}

.upload-btn {
  margin-top: 2px;
}

.upload-feedback {
  margin: 10px 0 0;
  color: var(--text-muted);
  font-size: var(--font-caption);
  line-height: 1.5;
}

.upload-feedback.error {
  color: var(--state-danger);
}

.upload-skeleton {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.upload-skeleton-icon {
  width: 44px;
  height: 54px;
}

.upload-skeleton-text {
  width: 64%;
  height: 16px;
}

.upload-skeleton-hint {
  width: 46%;
  height: 12px;
}
</style>
