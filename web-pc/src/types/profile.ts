export interface ProfileSummary {
  profile_id?: string | null
  name: string
  filename: string
  display_name?: string | null
  description?: string | null
  size: number
  created_at: string
  updated_at: string
  is_current: boolean
}

export interface ProfileDetail extends ProfileSummary {
  content: string
  config?: Record<string, unknown> | null
}

export interface CurrentProfileResponse {
  source: string
  profile_id?: string | null
  config: Record<string, unknown>
  content?: string
}

export interface DefaultProfileTemplate {
  config: Record<string, unknown>
  content: string
}

export interface CreateProfilePayload {
  content: string
  filename?: string
  profile_id?: string
  display_name?: string
  description?: string
  set_as_current?: boolean
  overwrite?: boolean
}

export interface UpdateProfilePayload {
  content: string
  filename?: string
  display_name?: string
  description?: string
  set_as_current?: boolean
}

export interface CopyProfilePayload {
  target_filename: string
}

export interface ProfileActionResponse {
  success: boolean
  message: string
  profile_file?: string
  profile_id?: string
  current_profile_id?: string
}
