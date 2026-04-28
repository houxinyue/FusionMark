import { ref } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

export function usePdfViewer() {
  const pdfDocument = ref<any>(null)
  const currentPage = ref(1)
  const totalPages = ref(0)
  const zoomLevel = ref(1)

  async function loadPdf(url: string) {
    const loadingTask = pdfjsLib.getDocument(url)
    pdfDocument.value = await loadingTask.promise
    totalPages.value = pdfDocument.value.numPages
  }

  async function renderPage(canvas: HTMLCanvasElement, pageNumber = currentPage.value) {
    if (!pdfDocument.value) return

    const page = await pdfDocument.value.getPage(pageNumber)
    const rotation = page.rotate || 0
    const viewport = page.getViewport({ scale: zoomLevel.value, rotation })
    const context = canvas.getContext('2d')

    if (!context) return

    const isRotated = rotation % 180 !== 0
    if (isRotated) {
      canvas.width = viewport.height
      canvas.height = viewport.width
      context.save()
      context.translate(canvas.width / 2, canvas.height / 2)
      context.rotate((rotation * Math.PI) / 180)
      context.translate(-viewport.width / 2, -viewport.height / 2)
    } else {
      canvas.width = viewport.width
      canvas.height = viewport.height
    }

    context.clearRect(0, 0, canvas.width, canvas.height)

    await page.render({
      canvasContext: context,
      viewport,
    }).promise

    if (isRotated) {
      context.restore()
    }

    currentPage.value = pageNumber
  }

  function nextPage() {
    if (currentPage.value < totalPages.value) {
      currentPage.value++
    }
  }

  function prevPage() {
    if (currentPage.value > 1) {
      currentPage.value--
    }
  }

  function zoomIn() {
    zoomLevel.value = Math.min(zoomLevel.value + 0.25, 3)
  }

  function zoomOut() {
    zoomLevel.value = Math.max(zoomLevel.value - 0.25, 0.5)
  }

  function destroy() {
    if (pdfDocument.value) {
      pdfDocument.value.destroy()
      pdfDocument.value = null
    }
    currentPage.value = 1
    totalPages.value = 0
    zoomLevel.value = 1
  }

  return {
    pdfDocument,
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
  }
}
