export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type StageName = 'mineru' | 'extraction' | 'highlight'

export type StageState = 'pending' | 'running' | 'completed' | 'failed' | 'done' | 'processing'

export interface StageProgress {
  state: StageState
  progress: number
  logs: string[]
}

export interface TaskProgress {
  stage: StageName | 'pending' | 'completed' | 'failed'
  stage_progress: number
  overall_progress: number
  mineru: StageProgress
  extraction: StageProgress
  highlight: StageProgress
}

export interface TaskResult {
  output_path?: string
  category_counts?: Record<string, number>
  objects?: Record<string, unknown>
}

export interface TaskDetail {
  task_id: string
  status: TaskStatus
  message?: string
  progress?: TaskProgress
  result?: TaskResult
}

export interface TaskSnapshot {
  task_id?: string
  status?: TaskStatus
  stage?: TaskProgress['stage']
  stage_progress?: number
  overall_progress?: number
  mineru?: Partial<StageProgress>
  extraction?: Partial<StageProgress>
  highlight?: Partial<StageProgress>
  progress?: Partial<TaskProgress>
  message?: string
  result?: TaskResult | null
}

export interface CreateTaskPayload {
  document_url: string
  model?: string
  enable_ocr?: boolean
  enable_formula?: boolean
  enable_table?: boolean
  language?: string
  output_filename?: string | null
  custom_title?: string | null
  custom_prompt?: string | null
}

export interface CreateTaskResponse {
  task_id: string
  status: TaskStatus
  message: string
  created_at: string
  updated_at?: string | null
  result?: TaskResult | null
}

export interface TaskListItem {
  task_id: string
  document_url: string
  status: TaskStatus
  stage: string
  overall_progress: number
  message?: string
  created_at: string
  updated_at: string
  result?: TaskResult | null
}

export interface TaskListResponse {
  total: number
  limit: number
  offset: number
  tasks: TaskListItem[]
}
