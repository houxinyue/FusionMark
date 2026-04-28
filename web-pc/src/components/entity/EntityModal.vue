<template>
  <n-modal
    :show="visible"
    title="文本实体回溯"
    preset="card"
    style="width: min(920px, calc(100vw - 32px))"
    @update:show="emit('update:visible', $event)"
  >
    <div v-if="loading" class="loading-state">正在加载提取结果...</div>

    <template v-else>
      <div class="artifact-actions">
        <a
          v-if="entitiesDownloadUrl"
          class="artifact-download"
          :href="entitiesDownloadUrl"
          target="_blank"
          rel="noopener noreferrer"
          download
        >
          下载实体 JSONL
        </a>
      </div>

      <iframe
        v-if="htmlContent"
        :srcdoc="htmlContent"
        class="entity-html-frame"
        sandbox="allow-same-origin allow-scripts"
      ></iframe>
      <div v-else class="empty-state">暂无 LangExtract HTML 可视化结果</div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { NModal } from 'naive-ui'

defineProps<{
  visible: boolean
  loading?: boolean
  htmlContent?: string
  entitiesDownloadUrl?: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()
</script>

<style scoped>
.artifact-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
}

.artifact-download {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: var(--radius-md);
  background: var(--brand-orange);
  color: #ffffff;
  font-size: var(--font-caption);
  font-weight: 800;
  text-decoration: none;
}

.artifact-download:hover {
  background: var(--brand-orange-soft);
}

.entity-html-frame {
  width: 100%;
  height: min(620px, 68vh);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background-color: white;
}

.empty-state,
.loading-state {
  text-align: center;
  padding: 48px 0;
  color: var(--text-muted);
  font-size: var(--font-body);
}
</style>
