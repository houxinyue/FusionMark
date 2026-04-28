export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type StageName = 'mineru' | 'extraction' | 'highlight'

export type StageState = 'pending' | 'running' | 'completed' | 'failed' | 'done'

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
}

export interface TaskDetail {
  task_id: string
  status: TaskStatus
  message?: string
  progress?: TaskProgress
  result?: TaskResult
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
