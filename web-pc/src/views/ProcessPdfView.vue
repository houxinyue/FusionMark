<template>
  <div class="process-page">
    <aside class="workbench-rail input-rail">
      <div class="rail-header">
        <span class="rail-kicker">Input</span>
        <h2>文档入口</h2>
      </div>
      <PdfUpload :loading="taskStore.isProcessing" />
      <UrlSubmit />
    </aside>

    <section class="pdf-workspace">
      <PdfToolbar
        :current-page="pdfState.currentPage"
        :total-pages="pdfState.totalPages"
        :zoom-level="pdfState.zoomLevel"
        :show-download="taskStore.status === 'completed'"
        @prev="pdfViewerRef?.goPrev()"
        @next="pdfViewerRef?.goNext()"
        @zoom-in="pdfViewerRef?.zoomInPage()"
        @zoom-out="pdfViewerRef?.zoomOutPage()"
        @download="openDownload"
      />
      <PdfViewer
        ref="pdfViewerRef"
        :url="highlightPdfUrl"
        @state-change="updatePdfState"
      />
    </section>

    <aside class="workbench-rail inspect-rail">
      <div class="rail-header">
        <span class="rail-kicker">Inspect</span>
        <h2>处理状态</h2>
      </div>
      <ProgressCard />
      <EntityTraceButton
        :disabled="taskStore.status !== 'completed'"
        :loading="entityLoading"
        :hint="taskStore.status === 'completed' ? '任务已完成，可查看结构化提取产物。' : '任务完成后可查看结构化提取产物。'"
        @click="openEntityModal"
      />
    </aside>

    <EntityModal
      v-model:visible="entityModalVisible"
      :loading="entityLoading"
      :html-content="entityHtml"
      :entities-download-url="entitiesDownloadUrl"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import {
  fetchArtifactText,
  getEntitiesArtifactUrl,
  getHighlightPdfArtifactUrl,
  getLangExtractHtmlUrl,
  getTaskDownloadUrl,
} from '@/api/taskApi'
import { useTaskStore } from '@/stores/taskStore'
import PdfUpload from '@/components/upload/PdfUpload.vue'
import UrlSubmit from '@/components/upload/UrlSubmit.vue'
import ProgressCard from '@/components/progress/ProgressCard.vue'
import EntityTraceButton from '@/components/entity/EntityTraceButton.vue'
import PdfToolbar from '@/components/pdf/PdfToolbar.vue'
import PdfViewer from '@/components/pdf/PdfViewer.vue'
import EntityModal from '@/components/entity/EntityModal.vue'

const taskStore = useTaskStore()
const pdfViewerRef = ref<InstanceType<typeof PdfViewer> | null>(null)
const pdfState = reactive({
  currentPage: 1,
  totalPages: 0,
  zoomLevel: 1,
  loading: false,
})

function updatePdfState(state: { currentPage: number; totalPages: number; zoomLevel: number; loading: boolean }) {
  Object.assign(pdfState, state)
}

const entityModalVisible = ref(false)
const entityLoading = ref(false)
const entityHtml = ref('')

const highlightPdfUrl = computed(() => {
  if (taskStore.status !== 'completed' || !taskStore.currentTaskId) {
    return ''
  }
  return getHighlightPdfArtifactUrl(taskStore.currentTaskId)
})

const entitiesDownloadUrl = computed(() => {
  if (taskStore.status !== 'completed' || !taskStore.currentTaskId) {
    return ''
  }
  return getEntitiesArtifactUrl(taskStore.currentTaskId)
})

function openDownload() {
  if (!taskStore.currentTaskId) return
  window.open(getTaskDownloadUrl(taskStore.currentTaskId), '_blank', 'noopener,noreferrer')
}

async function openEntityModal() {
  if (taskStore.status !== 'completed' || !taskStore.currentTaskId) return

  entityModalVisible.value = true
  entityLoading.value = true

  try {
    entityHtml.value = await fetchArtifactText(getLangExtractHtmlUrl(taskStore.currentTaskId))
  } catch (e) {
    console.error('Load entity artifacts failed:', e)
    entityHtml.value = ''
  } finally {
    entityLoading.value = false
  }
}
</script>

<style scoped>
.process-page {
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(420px, 1fr) minmax(280px, 340px);
  gap: 12px;
  flex: 1;
  min-height: 0;
  padding: 12px;
  overflow: hidden;
}

.workbench-rail,
.pdf-workspace {
  min-height: 0;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-rail);
  box-shadow: var(--shadow-sm);
  backdrop-filter: var(--backdrop-panel);
}

.workbench-rail {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  overflow-y: auto;
}

.pdf-workspace {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(241, 245, 249, 0.94)),
    var(--surface-canvas);
}

.rail-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-subtle);
}

.rail-kicker {
  color: var(--brand-orange-soft);
  font-size: var(--font-tiny);
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.rail-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-headline);
  line-height: 1.25;
}

@media (max-width: 1360px) {
  .process-page {
    grid-template-columns: minmax(260px, 300px) minmax(380px, 1fr) minmax(250px, 300px);
  }
}

@media (max-width: 1120px) {
  .process-page {
    grid-template-columns: minmax(280px, 340px) minmax(420px, 1fr);
    grid-template-rows: minmax(0, 1fr) auto;
    overflow-y: auto;
  }

  .inspect-rail {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1fr 320px;
    align-items: start;
  }

  .inspect-rail .rail-header {
    grid-column: 1 / -1;
  }
}

@media (max-width: 820px) {
  .process-page {
    grid-template-columns: 1fr;
    overflow-y: auto;
  }

  .pdf-workspace {
    min-height: 520px;
  }

  .inspect-rail {
    display: flex;
  }
}
</style>
