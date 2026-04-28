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
        :current-page="1"
        :total-pages="0"
        :zoom-level="1"
      />
      <PdfViewer />
    </section>

    <aside class="workbench-rail inspect-rail">
      <div class="rail-header">
        <span class="rail-kicker">Inspect</span>
        <h2>处理状态</h2>
      </div>
      <ProgressCard />
      <EntityTraceButton />
    </aside>

    <EntityModal :visible="false" />
  </div>
</template>

<script setup lang="ts">
import { useTaskStore } from '@/stores/taskStore'
import PdfUpload from '@/components/upload/PdfUpload.vue'
import UrlSubmit from '@/components/upload/UrlSubmit.vue'
import ProgressCard from '@/components/progress/ProgressCard.vue'
import EntityTraceButton from '@/components/entity/EntityTraceButton.vue'
import PdfToolbar from '@/components/pdf/PdfToolbar.vue'
import PdfViewer from '@/components/pdf/PdfViewer.vue'
import EntityModal from '@/components/entity/EntityModal.vue'

const taskStore = useTaskStore()
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
