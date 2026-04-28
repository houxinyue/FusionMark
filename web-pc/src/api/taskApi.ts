import { http } from './http'
import type { CreateTaskPayload, CreateTaskResponse, TaskDetail } from '@/types/task'

export async function createTask(payload: CreateTaskPayload): Promise<CreateTaskResponse> {
  return http.post('/api/v1/tasks', payload) as unknown as Promise<CreateTaskResponse>
}

export async function getTaskDetail(taskId: string): Promise<TaskDetail> {
  return http.get(`/api/v1/tasks/${taskId}`) as unknown as Promise<TaskDetail>
}

export function getTaskDownloadUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/download`
}

export function getLangExtractHtmlUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/artifacts/langextract_html`
}

export function getEntitiesArtifactUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/artifacts/entities`
}

export function getHighlightPdfArtifactUrl(taskId: string) {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/${taskId}/artifacts/highlight_pdf`
}

export async function fetchArtifactText(url: string): Promise<string> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Artifact request failed: ${response.status}`)
  }
  return response.text()
}
