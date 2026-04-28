export type ProgressStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface LogEntry {
  key: string
  stage: string
  text: string
  level: 'info' | 'failed'
  time: string
}
