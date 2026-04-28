import { onBeforeUnmount } from 'vue'
import { useTaskStore } from '@/stores/taskStore'

export function useTaskWebSocket() {
  const taskStore = useTaskStore()
  let ws: WebSocket | null = null

  function connect(taskId: string) {
    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL
    ws = new WebSocket(`${wsBaseUrl}/ws/${taskId}`)

    ws.onopen = () => {
      console.log('[WebSocket] 已连接')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'progress' || data.type === 'connected') {
          taskStore.progress = data.data.progress
          taskStore.status = data.data.status
        }
      } catch (e) {
        console.error('[WebSocket] 解析消息失败:', e)
      }
    }

    ws.onerror = () => {
      taskStore.status = 'failed'
    }

    ws.onclose = () => {
      console.log('[WebSocket] 已断开')
    }
  }

  function close() {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  onBeforeUnmount(() => {
    close()
  })

  return {
    connect,
    close,
  }
}
