import { onBeforeUnmount } from 'vue'
import { getTaskDetail } from '@/api/taskApi'
import { useTaskStore } from '@/stores/taskStore'
import type { TaskSnapshot } from '@/types/task'

type TaskSocketMessage =
  | { type: 'connected'; data?: TaskSnapshot }
  | { type: 'progress'; data?: TaskSnapshot }
  | { type: 'heartbeat' }
  | { type: 'error'; data?: { message?: string } }
  | { type: string; data?: unknown }

export function useTaskWebSocket() {
  const taskStore = useTaskStore()
  let ws: WebSocket | null = null
  let manualClose = false

  async function applyFallbackStatus(taskId: string) {
    try {
      const detail = await getTaskDetail(taskId)
      taskStore.applyTaskSnapshot(detail)
    } catch (e) {
      console.error('[WebSocket] 状态兜底查询失败:', e)
      taskStore.failTask('实时连接中断，且无法查询任务状态')
    }
  }

  function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null
  }

  function handleMessage(message: TaskSocketMessage, taskId: string) {
    if (message.type === 'heartbeat') {
      return
    }

    if (message.type === 'connected' || message.type === 'progress') {
      if (isRecord(message.data) && !('error' in message.data)) {
        taskStore.applyTaskSnapshot(message.data)
      } else if (message.type === 'connected') {
        taskStore.failTask('任务不存在或无法连接实时进度')
      }
      return
    }

    if (message.type === 'error') {
      const errorMessage = isRecord(message.data) && typeof message.data.message === 'string'
        ? message.data.message
        : '实时进度返回错误'
      taskStore.failTask(errorMessage)
      close()
      return
    }

    console.debug('[WebSocket] 忽略未知消息:', message, taskId)
  }

  function connect(taskId: string) {
    close()
    manualClose = false

    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL
    ws = new WebSocket(`${wsBaseUrl}/ws/${taskId}`)

    ws.onopen = () => {
      console.log('[WebSocket] 已连接')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskSocketMessage
        handleMessage(data, taskId)
      } catch (e) {
        console.error('[WebSocket] 解析消息失败:', e)
      }
    }

    ws.onerror = () => {
      console.warn('[WebSocket] 连接错误，准备查询任务详情兜底')
    }

    ws.onclose = () => {
      console.log('[WebSocket] 已断开')
      if (!manualClose && taskStore.isProcessing) {
        void applyFallbackStatus(taskId)
      }
    }
  }

  function requestStatus() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'get_status' }))
    }
  }

  function close() {
    if (ws) {
      manualClose = true
      ws.onclose = null
      ws.close()
      ws = null
    }
  }

  onBeforeUnmount(() => {
    close()
  })

  return {
    connect,
    requestStatus,
    close,
  }
}
