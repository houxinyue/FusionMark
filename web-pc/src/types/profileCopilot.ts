export interface CopilotMessage {
  role: 'user' | 'assistant' | string
  content: string
  created_at: string
}

export interface CopilotValidationResult {
  valid: boolean
  errors: string[]
  config?: Record<string, unknown> | null
}

export interface CopilotReferencedProfile {
  profile_id: string
  display_name: string
  description?: string | null
  score: number
  summary: string
}

export interface CopilotSessionResponse {
  session_id: string
  user_id: string
  messages: CopilotMessage[]
  draft_yaml: string
  validation: CopilotValidationResult
  referenced_profiles: CopilotReferencedProfile[]
  created_at: string
  updated_at: string
  assistant_message?: string
  rejected?: boolean
  generation_error?: boolean
}

export interface CopilotMessagePayload {
  message: string
}

export interface CopilotValidatePayload {
  draft_yaml?: string
}

