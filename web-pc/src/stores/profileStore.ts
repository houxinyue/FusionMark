import { defineStore } from 'pinia'
import {
  activateProfile,
  copyProfile,
  createProfile,
  deleteProfile,
  getCurrentProfile,
  getDefaultProfileTemplate,
  getProfileDetail,
  listProfiles,
  updateProfile,
} from '@/api/profileApi'
import type { CurrentProfileResponse, ProfileDetail, ProfileSummary } from '@/types/profile'

type EditorMode = 'existing' | 'new'

function extractApiError(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

function resolveProfileId(profile: Pick<ProfileSummary, 'profile_id' | 'name'>) {
  return profile.profile_id || profile.name
}

function deriveDisplayName(filename: string) {
  return filename.replace(/\.(yaml|yml)$/i, '')
}

export const useProfileStore = defineStore('profile', {
  state: () => ({
    profiles: [] as ProfileSummary[],
    selectedProfileId: null as string | null,
    originalProfile: null as ProfileDetail | null,
    currentProfile: null as CurrentProfileResponse | null,
    editorMode: 'new' as EditorMode,
    draftFilename: '',
    draftDisplayName: '',
    draftDescription: '',
    draftContent: '',
    defaultTemplateContent: '',
    loadingList: false,
    loadingDetail: false,
    saving: false,
    activating: false,
    deleting: false,
    copying: false,
    uploading: false,
    statusMessage: '',
    errorMessage: '',
  }),

  getters: {
    selectedProfile(state) {
      if (!state.selectedProfileId) return null
      return state.profiles.find((profile) => resolveProfileId(profile) === state.selectedProfileId) || null
    },

    hasSelection(): boolean {
      return this.editorMode === 'existing' && !!this.selectedProfileId
    },

    isDirty(state): boolean {
      if (state.editorMode === 'new') {
        return Boolean(
          state.draftFilename.trim() ||
            state.draftDisplayName.trim() ||
            state.draftDescription.trim() ||
            state.draftContent.trim(),
        )
      }

      if (!state.originalProfile) {
        return false
      }

      return (
        state.draftFilename !== state.originalProfile.filename ||
        (state.draftDisplayName || '') !== (state.originalProfile.display_name || '') ||
        (state.draftDescription || '') !== (state.originalProfile.description || '') ||
        state.draftContent !== state.originalProfile.content
      )
    },

    isBusy(): boolean {
      return (
        this.loadingList ||
        this.loadingDetail ||
        this.saving ||
        this.activating ||
        this.deleting ||
        this.copying ||
        this.uploading
      )
    },

    draftSize(state): number {
      return new Blob([state.draftContent]).size
    },
  },

  actions: {
    clearMessages() {
      this.statusMessage = ''
      this.errorMessage = ''
    },

    applyDetail(detail: ProfileDetail) {
      this.editorMode = 'existing'
      this.selectedProfileId = resolveProfileId(detail)
      this.originalProfile = detail
      this.draftFilename = detail.filename
      this.draftDisplayName = detail.display_name || ''
      this.draftDescription = detail.description || ''
      this.draftContent = detail.content
    },

    startNewProfile() {
      this.editorMode = 'new'
      this.selectedProfileId = null
      this.originalProfile = null
      this.draftFilename = ''
      this.draftDisplayName = ''
      this.draftDescription = ''
      this.draftContent = ''
      this.clearMessages()
    },

    async loadDefaultTemplate() {
      if (this.defaultTemplateContent) return
      const template = await getDefaultProfileTemplate()
      this.defaultTemplateContent = template.content
    },

    async loadCurrentProfile() {
      this.currentProfile = await getCurrentProfile()
    },

    async loadProfiles() {
      this.loadingList = true
      try {
        this.profiles = await listProfiles()
      } finally {
        this.loadingList = false
      }
    },

    async bootstrap() {
      this.clearMessages()
      await Promise.all([this.loadDefaultTemplate(), this.loadProfiles(), this.loadCurrentProfile()])

      const currentId = this.currentProfile?.profile_id || null
      const nextProfile =
        this.profiles.find((profile) => resolveProfileId(profile) === currentId) ||
        this.profiles.find((profile) => profile.is_current) ||
        this.profiles[0]

      if (nextProfile) {
        await this.selectProfile(resolveProfileId(nextProfile))
        return
      }

      this.startNewProfile()
    },

    async selectProfile(profileId: string) {
      this.loadingDetail = true
      this.clearMessages()
      try {
        const detail = await getProfileDetail(profileId)
        this.applyDetail(detail)
      } catch (error) {
        this.errorMessage = extractApiError(error, '加载配置失败')
        throw error
      } finally {
        this.loadingDetail = false
      }
    },

    async refreshSelection() {
      await Promise.all([this.loadProfiles(), this.loadCurrentProfile()])

      if (this.editorMode === 'new') {
        return
      }

      const selectedId = this.selectedProfileId
      const nextProfile =
        this.profiles.find((profile) => resolveProfileId(profile) === selectedId) ||
        this.profiles.find((profile) => profile.is_current) ||
        this.profiles[0]

      if (nextProfile) {
        await this.selectProfile(resolveProfileId(nextProfile))
      } else {
        this.startNewProfile()
      }
    },

    async saveDraft(setAsCurrent = false) {
      const filename = this.draftFilename.trim()
      if (!filename) {
        this.errorMessage = '请填写配置文件名'
        return null
      }
      if (!this.draftContent.trim()) {
        this.errorMessage = 'YAML 内容不能为空'
        return null
      }

      this.saving = true
      this.clearMessages()

      try {
        const payload = {
          filename,
          display_name: this.draftDisplayName.trim() || deriveDisplayName(filename),
          description: this.draftDescription,
          content: this.draftContent,
          set_as_current: setAsCurrent,
        }

        const detail =
          this.editorMode === 'new'
            ? await createProfile({ ...payload, overwrite: false })
            : await updateProfile(this.selectedProfileId as string, payload)

        this.applyDetail(detail)
        await Promise.all([this.loadProfiles(), this.loadCurrentProfile()])
        this.statusMessage = setAsCurrent ? '配置已保存并激活' : '配置已保存'
        return detail
      } catch (error) {
        this.errorMessage = extractApiError(error, '保存配置失败')
        throw error
      } finally {
        this.saving = false
      }
    },

    async activateSelected() {
      if (!this.selectedProfileId) return

      this.activating = true
      this.clearMessages()

      try {
        await activateProfile(this.selectedProfileId)
        await Promise.all([this.loadProfiles(), this.loadCurrentProfile()])
        this.statusMessage = '配置已激活'
      } catch (error) {
        this.errorMessage = extractApiError(error, '激活配置失败')
        throw error
      } finally {
        this.activating = false
      }
    },

    async deleteSelected() {
      if (!this.selectedProfileId) return

      this.deleting = true
      this.clearMessages()

      try {
        await deleteProfile(this.selectedProfileId)
        await this.refreshSelection()
        this.statusMessage = '配置已删除'
      } catch (error) {
        this.errorMessage = extractApiError(error, '删除配置失败')
        throw error
      } finally {
        this.deleting = false
      }
    },

    async copySelected(targetFilename: string) {
      if (!this.selectedProfileId) return null

      this.copying = true
      this.clearMessages()

      try {
        const detail = await copyProfile(this.selectedProfileId, { target_filename: targetFilename })
        await Promise.all([this.loadProfiles(), this.loadCurrentProfile()])
        this.applyDetail(detail)
        this.statusMessage = '配置已复制'
        return detail
      } catch (error) {
        this.errorMessage = extractApiError(error, '复制配置失败')
        throw error
      } finally {
        this.copying = false
      }
    },

    async uploadFile(file: File, overwrite = false) {
      this.uploading = true
      this.clearMessages()

      try {
        const content = await file.text()
        const detail = await createProfile({
          filename: file.name,
          content,
          description: '',
          display_name: deriveDisplayName(file.name),
          overwrite,
          set_as_current: false,
        })
        await Promise.all([this.loadProfiles(), this.loadCurrentProfile()])
        this.applyDetail(detail)
        this.statusMessage = overwrite ? '配置已覆盖上传' : '配置已上传'
        return detail
      } catch (error) {
        this.errorMessage = extractApiError(error, '上传配置失败')
        throw error
      } finally {
        this.uploading = false
      }
    },
  },
})
