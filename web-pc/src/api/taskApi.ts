import { http } from './http'
import type { CreateTaskPayload, TaskDetail } from '@/types/task'

export function createTask(payload: CreateTaskPayload) {
  return http.post<{ task_id: string }>('/api/v1/tasks', payload)
}

export function getTaskDetail(taskId: string) {
  return http.get<TaskDetail>(`/api/v1/tasks/${taskId}`)
}

export function getTaskDownloadUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/download`
}

export function getLangExtractHtmlUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/artifacts/langextract_html`
}
