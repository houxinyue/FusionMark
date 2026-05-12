import { http } from './http'
import type { CreateTaskPayload, CreateTaskResponse, TaskDetail, TaskListResponse } from '@/types/task'

export async function createTask(payload: CreateTaskPayload): Promise<CreateTaskResponse> {
  return http.post('/api/v1/tasks', payload) as unknown as Promise<CreateTaskResponse>
}

export interface UploadTaskPayload {
  file: File
  model?: string
  enable_ocr?: boolean
  enable_formula?: boolean
  enable_table?: boolean
  language?: string
  output_filename?: string | null
  custom_title?: string | null
  custom_prompt?: string | null
}

export async function uploadTask(payload: UploadTaskPayload): Promise<CreateTaskResponse> {
  const formData = new FormData()
  formData.append('file', payload.file)
  if (payload.model !== undefined) formData.append('model', payload.model)
  if (payload.enable_ocr !== undefined) formData.append('enable_ocr', String(payload.enable_ocr))
  if (payload.enable_formula !== undefined) formData.append('enable_formula', String(payload.enable_formula))
  if (payload.enable_table !== undefined) formData.append('enable_table', String(payload.enable_table))
  if (payload.language !== undefined) formData.append('language', payload.language)
  if (payload.output_filename) formData.append('output_filename', payload.output_filename)
  if (payload.custom_title) formData.append('custom_title', payload.custom_title)
  if (payload.custom_prompt) formData.append('custom_prompt', payload.custom_prompt)

  return http.post('/api/v1/tasks/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }) as unknown as Promise<CreateTaskResponse>
}

export async function getTaskDetail(taskId: string): Promise<TaskDetail> {
  return http.get(`/api/v1/tasks/${taskId}`) as unknown as Promise<TaskDetail>
}

export async function listTasks(limit = 20, offset = 0): Promise<TaskListResponse> {
  return http.get(`/api/v1/tasks?limit=${limit}&offset=${offset}`) as unknown as Promise<TaskListResponse>
}

export async function deleteTask(taskId: string): Promise<void> {
  await http.delete(`/api/v1/tasks/${taskId}`)
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
