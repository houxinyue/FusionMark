import { defineStore } from 'pinia'
import {
  createCopilotSession,
  sendCopilotMessage,
  validateCopilotDraft,
} from '@/api/profileCopilotApi'
import type {
  CopilotMessage,
  CopilotReferencedProfile,
  CopilotValidationResult,
} from '@/types/profileCopilot'

function extractApiError(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export const useProfileCopilotStore = defineStore('profileCopilot', {
  state: () => ({
    sessionId: null as string | null,
    messages: [] as CopilotMessage[],
    draftYaml: '',
    validation: { valid: false, errors: [] } as CopilotValidationResult,
    referencedProfiles: [] as CopilotReferencedProfile[],
    loading: false,
    validating: false,
    rejected: false,
    generationError: false,
    errorMessage: '',
  }),

  getters: {
    canApply(state): boolean {
      return Boolean(state.draftYaml.trim()) && state.validation.valid
    },
  },

  actions: {
    applyResponse(response: {
      session_id: string
      messages: CopilotMessage[]
      draft_yaml: string
      validation: CopilotValidationResult
      referenced_profiles: CopilotReferencedProfile[]
      rejected?: boolean
      generation_error?: boolean
    }) {
      this.sessionId = response.session_id
      this.messages = response.messages || []
      this.draftYaml = response.draft_yaml || ''
      this.validation = response.validation || { valid: false, errors: [] }
      this.referencedProfiles = response.referenced_profiles || []
      this.rejected = Boolean(response.rejected)
      this.generationError = Boolean(response.generation_error)
    },

    async ensureSession() {
      if (this.sessionId) return this.sessionId
      const response = await createCopilotSession()
      this.applyResponse(response)
      return this.sessionId as string
    },

    async sendMessage(message: string) {
      const content = message.trim()
      if (!content) return
      this.loading = true
      this.errorMessage = ''
      try {
        const sessionId = await this.ensureSession()
        const response = await sendCopilotMessage(sessionId, { message: content })
        this.applyResponse(response)
      } catch (error) {
        this.errorMessage = extractApiError(error, 'Copilot 生成失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async validateDraft(draftYaml?: string) {
      this.validating = true
      this.errorMessage = ''
      try {
        const sessionId = await this.ensureSession()
        const response = await validateCopilotDraft(sessionId, { draft_yaml: draftYaml })
        this.applyResponse(response)
      } catch (error) {
        this.errorMessage = extractApiError(error, 'Copilot 校验失败')
        throw error
      } finally {
        this.validating = false
      }
    },

    reset() {
      this.sessionId = null
      this.messages = []
      this.draftYaml = ''
      this.validation = { valid: false, errors: [] }
      this.referencedProfiles = []
      this.rejected = false
      this.generationError = false
      this.errorMessage = ''
    },
  },
})

