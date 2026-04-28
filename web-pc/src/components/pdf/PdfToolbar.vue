<template>
  <div class="preview-toolbar">
    <div class="toolbar-left">
      <n-button size="small" quaternary @click="emit('prev')">‹</n-button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <n-button size="small" quaternary @click="emit('next')">›</n-button>
    </div>
    <div class="toolbar-right">
      <n-button size="small" quaternary @click="emit('zoomOut')">−</n-button>
      <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
      <n-button size="small" quaternary @click="emit('zoomIn')">+</n-button>
      <n-button type="primary" size="small" v-if="showDownload" @click="emit('download')">
        下载结果
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'

defineProps<{
  currentPage: number
  totalPages: number
  zoomLevel: number
  showDownload?: boolean
}>()

const emit = defineEmits<{
  prev: []
  next: []
  zoomIn: []
  zoomOut: []
  download: []
}>()
</script>

<style scoped>
.preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 44px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.84);
  border-bottom: 1px solid var(--border-subtle);
  backdrop-filter: var(--backdrop-panel);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-info,
.zoom-level {
  min-width: 64px;
  font-size: var(--font-caption);
  color: var(--text-secondary);
  text-align: center;
}

.zoom-level {
  min-width: 46px;
}
</style>
