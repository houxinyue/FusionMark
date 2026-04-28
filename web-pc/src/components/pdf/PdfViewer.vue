<template>
  <div class="pdf-viewer">
    <div v-if="!props.url" class="empty-state" aria-live="polite">
      <div class="empty-illustration">
        <div class="orbit-system">
          <div class="orbit-ring ring-one"></div>
          <div class="orbit-ring ring-two"></div>
          <div class="orbit-core">
            <img src="@/assets/images/fusion_mark_orbit_core.svg" alt="FusionMark" />
          </div>
          <div class="orbit-node node-mineru" aria-label="MinerU 提取内容"></div>
          <div class="orbit-node node-langextract" aria-label="LangExtract 识别实体"></div>
          <div class="orbit-node node-output" aria-label="FusionMark 输出高亮 PDF"></div>
        </div>
      </div>
      <p class="empty-text">上传文档开始智能解析</p>
      <p class="empty-hint">MinerU 提取内容，LangExtract 识别实体，FusionMark 输出高亮 PDF</p>
    </div>

    <div v-else-if="isLoading" class="pdf-skeleton">
      <div class="skeleton skeleton-block pdf-skeleton-page" />
      <div class="skeleton skeleton-block pdf-skeleton-line" style="width: 80%;" />
      <div class="skeleton skeleton-block pdf-skeleton-line" style="width: 60%;" />
      <div class="skeleton skeleton-block pdf-skeleton-line" style="width: 70%;" />
    </div>

    <div v-else-if="loadError" class="pdf-error">
      <p>高亮 PDF 预览加载失败</p>
      <span>{{ loadError }}</span>
    </div>

    <canvas v-show="props.url && !isLoading && !loadError" ref="canvasRef" class="pdf-canvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { usePdfViewer } from '@/composables/usePdfViewer'

const props = defineProps<{
  url?: string
}>()

const emit = defineEmits<{
  stateChange: [state: { currentPage: number; totalPages: number; zoomLevel: number; loading: boolean }]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const isLoading = ref(false)
const loadError = ref('')
const {
  currentPage,
  totalPages,
  zoomLevel,
  loadPdf,
  renderPage,
  nextPage,
  prevPage,
  zoomIn,
  zoomOut,
  destroy,
} = usePdfViewer()

function emitState() {
  emit('stateChange', {
    currentPage: currentPage.value,
    totalPages: totalPages.value,
    zoomLevel: zoomLevel.value,
    loading: isLoading.value,
  })
}

async function renderCurrentPage() {
  if (!canvasRef.value) return
  await renderPage(canvasRef.value)
  emitState()
}

async function goPrev() {
  prevPage()
  await renderCurrentPage()
}

async function goNext() {
  nextPage()
  await renderCurrentPage()
}

async function zoomInPage() {
  zoomIn()
  await renderCurrentPage()
}

async function zoomOutPage() {
  zoomOut()
  await renderCurrentPage()
}

watch(
  () => props.url,
  async (newUrl) => {
    loadError.value = ''
    if (!newUrl) {
      destroy()
      isLoading.value = false
      emitState()
      return
    }

    isLoading.value = true
    emitState()
    destroy()

    try {
      await loadPdf(newUrl)
      await nextTick()
      await renderCurrentPage()
    } catch (e) {
      console.error('PDF load error:', e)
      loadError.value = e instanceof Error ? e.message : '未知错误'
    } finally {
      isLoading.value = false
      emitState()
    }
  },
  { immediate: true },
)

defineExpose({
  goPrev,
  goNext,
  zoomInPage,
  zoomOutPage,
})
</script>

<style scoped>
.pdf-viewer {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 0;
  overflow: auto;
  position: relative;
  background:
    linear-gradient(rgba(148, 163, 184, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.035) 1px, transparent 1px),
    radial-gradient(circle at 50% 36%, rgba(249, 115, 22, 0.08), transparent 32%),
    var(--surface-canvas);
  background-size: 34px 34px, 34px 34px, auto, auto;
}

.pdf-canvas {
  max-width: 100%;
  box-shadow:
    0 18px 46px rgba(15, 23, 42, 0.18),
    0 0 0 1px rgba(148, 163, 184, 0.22);
  border-radius: var(--radius-sm);
  background: #ffffff;
}

.empty-state {
  width: min(560px, calc(100% - 32px));
  text-align: center;
}

.empty-illustration {
  width: 320px;
  height: 220px;
  margin: 0 auto 20px;
  position: relative;
}

.orbit-system {
  position: absolute;
  inset: 0;
}

.orbit-ring {
  position: absolute;
  left: 50%;
  top: 50%;
  border: 1px solid rgba(100, 116, 139, 0.2);
  border-radius: 50%;
  transform: translate(-50%, -50%) rotate(-12deg);
  pointer-events: none;
}

.ring-one {
  width: 230px;
  height: 116px;
}

.ring-two {
  width: 270px;
  height: 150px;
  border-color: rgba(249, 115, 22, 0.18);
  transform: translate(-50%, -50%) rotate(16deg);
}

.orbit-core {
  position: absolute;
  left: 50%;
  top: 50%;
  display: grid;
  place-items: center;
  width: 92px;
  height: 92px;
  border: 1px solid rgba(249, 115, 22, 0.22);
  border-radius: 50%;
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, 0.96), rgba(255, 237, 213, 0.56) 42%, rgba(249, 115, 22, 0.12)),
    #ffffff;
  box-shadow:
    0 18px 36px rgba(249, 115, 22, 0.14),
    inset 0 0 0 8px rgba(249, 115, 22, 0.04);
  transform: translate(-50%, -50%);
}

.orbit-core img {
  width: 74px;
  height: 74px;
  object-fit: contain;
  filter: drop-shadow(0 5px 10px rgba(249, 115, 22, 0.18));
}

.orbit-node {
  position: absolute;
  width: 14px;
  height: 14px;
  border: 3px solid #ffffff;
  border-radius: 50%;
  background: var(--text-subtle);
  box-shadow:
    0 4px 10px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(100, 116, 139, 0.12);
  animation: orbitDrift 5.2s ease-in-out infinite;
}

.node-mineru {
  left: 66px;
  top: 68px;
  background: #0ea5e9;
}

.node-langextract {
  right: 58px;
  top: 88px;
  animation-delay: -1.7s;
  background: #7c3aed;
}

.node-output {
  left: 150px;
  bottom: 46px;
  animation-delay: -3s;
  background: var(--brand-orange);
}

@keyframes orbitDrift {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(0, -6px, 0); }
}

.empty-text {
  font-size: var(--font-headline);
  font-weight: 750;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.empty-hint {
  max-width: 450px;
  margin: 0 auto;
  font-size: var(--font-body);
  color: var(--text-muted);
}

.pdf-skeleton {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  max-width: 600px;
  padding: 24px;
}

.pdf-skeleton-page {
  width: 100%;
  aspect-ratio: 3/4;
  max-height: 400px;
  border-radius: var(--radius-lg);
}

.pdf-skeleton-line {
  height: 12px;
  border-radius: var(--radius-sm);
}

.pdf-error {
  max-width: 420px;
  padding: 18px;
  border: 1px solid rgba(225, 29, 72, 0.22);
  border-radius: var(--radius-lg);
  background: rgba(255, 228, 230, 0.62);
  color: var(--state-danger);
  text-align: center;
}

.pdf-error p {
  margin: 0 0 6px;
  font-weight: 800;
}

.pdf-error span {
  color: var(--text-muted);
  font-size: var(--font-caption);
}

@media (max-width: 640px) {
  .empty-illustration {
    width: 280px;
  }

  .node-mineru {
    left: 46px;
  }

  .node-langextract {
    right: 38px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .orbit-node {
    animation: none;
  }
}
</style>
