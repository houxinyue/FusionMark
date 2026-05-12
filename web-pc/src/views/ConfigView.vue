<template>
  <div class="config-page">
    <aside class="config-rail profile-rail">
      <div class="rail-header">
        <div>
          <p class="rail-kicker">Profiles</p>
          <h2>配置清单</h2>
        </div>
        <div class="header-actions">
          <n-button size="small" quaternary :disabled="profileStore.isBusy" @click="handleRefresh">
            刷新
          </n-button>
          <n-button size="small" quaternary :disabled="profileStore.isBusy" @click="handleNew">
            新建
          </n-button>
          <n-button size="small" type="primary" :loading="profileStore.uploading" @click="triggerUpload">
            上传
          </n-button>
          <input
            ref="fileInputRef"
            class="hidden-input"
            type="file"
            accept=".yaml,.yml"
            @change="handleFilePicked"
          />
        </div>
      </div>

      <n-spin :show="profileStore.loadingList">
        <div v-if="profileStore.profiles.length" class="profile-list">
          <button
            v-for="profile in profileStore.profiles"
            :key="profile.profile_id || profile.name"
            type="button"
            class="profile-item"
            :class="{ selected: (profile.profile_id || profile.name) === profileStore.selectedProfileId && profileStore.editorMode === 'existing' }"
            @click="handleSelectProfile(profile.profile_id || profile.name)"
          >
            <div class="profile-item-top">
              <strong>{{ profile.display_name || profile.filename }}</strong>
              <n-tag v-if="profile.is_current" size="small" round type="warning">当前</n-tag>
            </div>
            <p class="profile-item-filename">{{ profile.filename }}</p>
            <p class="profile-item-description">{{ profile.description || '未填写说明' }}</p>
            <div class="profile-item-meta">
              <span>{{ formatBytes(profile.size) }}</span>
              <span>{{ formatTime(profile.updated_at) }}</span>
            </div>
          </button>
        </div>
        <n-empty v-else description="暂无配置，先新建或上传 YAML" size="small" class="empty-state" />
      </n-spin>
    </aside>

    <section class="config-editor">
      <div class="editor-header">
        <div>
          <p class="rail-kicker">Editor</p>
          <h2>{{ editorTitle }}</h2>
          <p class="editor-hint">
            YAML 原文会原样保存，注释和格式不会在后端被重写。
          </p>
        </div>
        <div class="editor-actions">
          <n-tag v-if="profileStore.editorMode === 'new'" size="small" round type="info">未入库</n-tag>
          <n-tag v-else-if="profileStore.isDirty" size="small" round type="warning">未保存</n-tag>
          <n-button
            size="small"
            :disabled="!canSaveChanges"
            :loading="profileStore.saving"
            @click="handleSave(false)"
          >
            保存
          </n-button>
          <n-button
            size="small"
            type="primary"
            :disabled="!canSave"
            :loading="profileStore.saving"
            @click="handleSave(true)"
          >
            保存并激活
          </n-button>
        </div>
      </div>

      <n-spin :show="profileStore.loadingDetail" class="editor-body">
        <div class="editor-form">
          <div class="field-grid">
            <label class="field">
              <span>文件名</span>
              <n-input
                v-model:value="profileStore.draftFilename"
                placeholder="例如: smart-report.yaml"
              />
            </label>
            <label class="field">
              <span>显示名</span>
              <n-input
                v-model:value="profileStore.draftDisplayName"
                placeholder="界面展示名称"
              />
            </label>
          </div>

          <label class="field">
            <span>说明</span>
            <n-input
              v-model:value="profileStore.draftDescription"
              type="textarea"
              placeholder="说明这个 profile 用于什么文档或提示词策略"
              :autosize="{ minRows: 2, maxRows: 4 }"
            />
          </label>

          <label class="field editor-field">
            <span>YAML</span>
            <textarea
              v-model="profileStore.draftContent"
              class="yaml-editor"
              spellcheck="false"
              placeholder="在这里编辑 YAML 配置..."
            />
          </label>

          <div class="copilot-entry">
            <div>
              <span class="copilot-entry-label">AI Copilot</span>
              <p>用自然语言生成或修改 Profile YAML 草稿，应用后再手动保存。</p>
            </div>
            <n-button type="primary" secondary @click="openCopilotDialog">
              智能生成配置
            </n-button>
          </div>
        </div>
      </n-spin>
    </section>

    <aside class="config-rail summary-rail">
      <div class="rail-header">
        <div>
          <p class="rail-kicker">Summary</p>
          <h2>状态与动作</h2>
        </div>
      </div>

      <div v-if="profileStore.editorMode !== 'new'" class="summary-group">
        <div class="summary-row">
          <span>来源</span>
          <strong>{{ profileStore.currentProfile?.source || 'default' }}</strong>
        </div>
        <div class="summary-row">
          <span>Profile ID</span>
          <strong>{{ profileStore.selectedProfileId || '未创建' }}</strong>
        </div>
        <div class="summary-row">
          <span>内容大小</span>
          <strong>{{ formatBytes(profileStore.draftSize) }}</strong>
        </div>
        <div class="summary-row">
          <span>更新时间</span>
          <strong>{{ selectedProfile ? formatTime(selectedProfile.updated_at) : '未保存' }}</strong>
        </div>
      </div>

      <div class="summary-group">
        <div class="summary-row">
          <span>校验</span>
          <strong>{{ validationLabel }}</strong>
        </div>
        <p v-if="profileStore.statusMessage" class="feedback success">{{ profileStore.statusMessage }}</p>
        <div v-if="topLevelKeys.length" class="key-list">
          <span v-for="item in topLevelKeys" :key="item" class="key-pill">{{ item }}</span>
        </div>
      </div>

      <div class="summary-actions">
        <n-button
          block
          :disabled="!profileStore.hasSelection"
          :loading="profileStore.copying"
          @click="openCopyDialog"
        >
          复制当前配置
        </n-button>
        <n-button
          block
          :disabled="!profileStore.hasSelection"
          @click="handleDownload"
        >
          下载 YAML
        </n-button>
        <n-button
          block
          secondary
          type="error"
          :disabled="!profileStore.hasSelection"
          :loading="profileStore.deleting"
          @click="handleDelete"
        >
          删除配置
        </n-button>
      </div>
    </aside>

    <n-modal v-model:show="copyDialogVisible" preset="card" title="复制配置" class="dialog-card">
      <div class="dialog-body">
        <n-input
          v-model:value="copyFilename"
          placeholder="例如: smart-report-copy.yaml"
          @keyup.enter="submitCopy"
        />
        <div class="dialog-actions">
          <n-button quaternary @click="copyDialogVisible = false">取消</n-button>
          <n-button type="primary" :loading="profileStore.copying" @click="submitCopy">创建副本</n-button>
        </div>
      </div>
    </n-modal>

    <n-modal v-model:show="overwriteDialogVisible" preset="card" title="覆盖上传" class="dialog-card">
      <div class="dialog-body">
        <p class="dialog-copy">
          同名配置已存在，继续上传会直接覆盖当前存储版本。
        </p>
        <div class="dialog-actions">
          <n-button quaternary @click="cancelOverwriteUpload">取消</n-button>
          <n-button type="primary" :loading="profileStore.uploading" @click="confirmOverwriteUpload">
            覆盖上传
          </n-button>
        </div>
      </div>
    </n-modal>

    <n-modal
      v-model:show="copilotDialogVisible"
      preset="card"
      title="Profile Copilot"
      class="copilot-dialog"
      style="width: min(720px, calc(100vw - 24px))"
      :bordered="false"
    >
      <ProfileCopilotPanel v-if="copilotDialogVisible" @apply-draft="handleApplyCopilotDraft" />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { NButton, NEmpty, NInput, NModal, NSpin, NTag, useDialog } from 'naive-ui'
import { getProfileDownloadUrl } from '@/api/profileApi'
import ProfileCopilotPanel from '@/components/config/ProfileCopilotPanel.vue'
import { useProfileCopilotStore } from '@/stores/profileCopilotStore'
import { useProfileStore } from '@/stores/profileStore'

const profileStore = useProfileStore()
const profileCopilotStore = useProfileCopilotStore()
const dialog = useDialog()
const fileInputRef = ref<HTMLInputElement | null>(null)
const copyDialogVisible = ref(false)
const overwriteDialogVisible = ref(false)
const copilotDialogVisible = ref(false)
const copyFilename = ref('')
const pendingUploadFile = ref<File | null>(null)

const selectedProfile = computed(() => profileStore.selectedProfile)
const editorTitle = computed(() => {
  if (profileStore.editorMode === 'new') {
    return profileStore.draftFilename || '新建配置'
  }
  return (
    profileStore.draftDisplayName ||
    profileStore.draftFilename ||
    selectedProfile.value?.filename ||
    '配置详情'
  )
})
const canSave = computed(
  () => Boolean(profileStore.draftFilename.trim()) && Boolean(profileStore.draftContent.trim()),
)
const canSaveChanges = computed(
  () => canSave.value && (profileStore.editorMode === 'new' || profileStore.isDirty),
)
const validationLabel = computed(() => {
  if (profileStore.loadingList || profileStore.loadingDetail) return '加载中'
  if (profileStore.saving) return '保存中'
  if (profileStore.errorMessage) return '校验未通过'
  if (profileStore.editorMode === 'new') {
    const hasDraft =
      Boolean(profileStore.draftFilename.trim()) ||
      Boolean(profileStore.draftDisplayName.trim()) ||
      Boolean(profileStore.draftDescription.trim()) ||
      Boolean(profileStore.draftContent.trim())
    if (!hasDraft) return '未创建'

    const isDefaultTemplateDraft =
      !profileStore.draftFilename.trim() &&
      !profileStore.draftDisplayName.trim() &&
      !profileStore.draftDescription.trim() &&
      Boolean(profileStore.defaultTemplateContent.trim()) &&
      profileStore.draftContent.trim() === profileStore.defaultTemplateContent.trim()

    return isDefaultTemplateDraft ? '模板未保存' : '待保存'
  }
  if (profileStore.isDirty) return '待保存'
  if (profileStore.statusMessage) return '已同步'
  if (profileStore.selectedProfileId || profileStore.originalProfile) return '已同步'
  return '未加载'
})
const topLevelKeys = computed(() =>
  profileStore.editorMode === 'new'
    ? []
    : Object.keys((profileStore.originalProfile?.config || profileStore.currentProfile?.config || {}) as Record<string, unknown>).slice(0, 8),
)

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

function formatTime(value?: string | null) {
  if (!value) return '未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function isConflictError(error: unknown) {
  return (error as { response?: { status?: number } })?.response?.status === 409
}

function resolveErrorDialogTitle(message: string) {
  if (message.includes('YAML') || message.includes('validation')) {
    return '配置校验失败'
  }
  return '操作失败'
}

function showErrorDialog(message: string) {
  dialog.error({
    title: resolveErrorDialogTitle(message),
    content: message,
    positiveText: '知道了',
    maskClosable: true,
  })
}

function confirmDiscardDraft() {
  if (!profileStore.isDirty) return true
  return window.confirm('当前编辑内容尚未保存，继续操作会丢失修改。')
}

async function handleRefresh() {
  try {
    await profileStore.refreshSelection()
  } catch (error) {
    console.error('Refresh profiles failed:', error)
  }
}

function handleNew() {
  if (!confirmDiscardDraft()) return
  profileStore.startNewProfile()
}

async function handleSelectProfile(profileId: string) {
  if (profileStore.editorMode === 'existing' && profileStore.selectedProfileId === profileId) return
  if (!confirmDiscardDraft()) return

  try {
    await profileStore.selectProfile(profileId)
  } catch (error) {
    console.error('Load profile detail failed:', error)
  }
}

async function handleSave(setAsCurrent: boolean) {
  try {
    await profileStore.saveDraft(setAsCurrent)
  } catch (error) {
    console.error('Save profile failed:', error)
  }
}

function openCopyDialog() {
  if (!selectedProfile.value) return
  const baseName = selectedProfile.value.filename.replace(/\.(yaml|yml)$/i, '')
  copyFilename.value = `${baseName}-copy.yaml`
  copyDialogVisible.value = true
}

async function submitCopy() {
  const target = copyFilename.value.trim()
  if (!target) return

  try {
    await profileStore.copySelected(target)
    copyDialogVisible.value = false
  } catch (error) {
    console.error('Copy profile failed:', error)
  }
}

function triggerUpload() {
  fileInputRef.value?.click()
}

async function handleFilePicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''

  if (!file) return
  if (!confirmDiscardDraft()) return

  try {
    await profileStore.uploadFile(file, false)
  } catch (error) {
    if (isConflictError(error)) {
      pendingUploadFile.value = file
      overwriteDialogVisible.value = true
      return
    }
    console.error('Upload profile failed:', error)
  }
}

async function confirmOverwriteUpload() {
  if (!pendingUploadFile.value) return

  try {
    await profileStore.uploadFile(pendingUploadFile.value, true)
    overwriteDialogVisible.value = false
    pendingUploadFile.value = null
  } catch (error) {
    console.error('Overwrite upload failed:', error)
  }
}

function cancelOverwriteUpload() {
  pendingUploadFile.value = null
  overwriteDialogVisible.value = false
}

function handleDownload() {
  if (!profileStore.selectedProfileId) return
  window.open(getProfileDownloadUrl(profileStore.selectedProfileId), '_blank', 'noopener,noreferrer')
}

function openCopilotDialog() {
  profileCopilotStore.reset()
  copilotDialogVisible.value = true
}

function handleApplyCopilotDraft(draftYaml: string) {
  profileStore.draftContent = draftYaml
  profileStore.statusMessage = 'Copilot 草稿已应用，请检查后保存'
  profileStore.errorMessage = ''
  copilotDialogVisible.value = false
}

async function handleDelete() {
  if (!profileStore.selectedProfileId) return
  if (!window.confirm('删除后不会自动恢复，确认继续吗？')) return

  try {
    await profileStore.deleteSelected()
  } catch (error) {
    console.error('Delete profile failed:', error)
  }
}

onMounted(async () => {
  try {
    await profileStore.bootstrap()
  } catch (error) {
    console.error('Bootstrap profiles failed:', error)
  }
})

watch(
  () => profileStore.errorMessage,
  (message) => {
    if (!message) return
    showErrorDialog(message)
  },
)
</script>

<style scoped>
.config-page {
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(520px, 1fr) minmax(260px, 320px);
  gap: 12px;
  flex: 1;
  min-height: 0;
  padding: 12px;
  overflow: hidden;
}

.config-rail,
.config-editor {
  min-height: 0;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-rail);
  box-shadow: var(--shadow-sm);
  backdrop-filter: var(--backdrop-panel);
}

.config-rail {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  overflow-y: auto;
}

.config-editor {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.editor-body :deep(.n-spin-container),
.editor-body :deep(.n-spin-content) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
}

.rail-header,
.editor-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
}

.rail-kicker {
  margin: 0 0 4px;
  color: var(--brand-orange-soft);
  font-size: var(--font-tiny);
  font-weight: 800;
  text-transform: uppercase;
}

.rail-header h2,
.editor-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-display);
}

.header-actions,
.editor-actions,
.dialog-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.hidden-input {
  display: none;
}

.profile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  background: var(--surface-sunken);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    background-color var(--transition-fast),
    transform var(--transition-fast);
}

.profile-item:hover {
  border-color: rgba(249, 115, 22, 0.34);
  background: rgba(255, 247, 237, 0.86);
  transform: translateY(-1px);
}

.profile-item.selected {
  border-color: rgba(249, 115, 22, 0.58);
  background: linear-gradient(180deg, rgba(255, 247, 237, 0.96), rgba(255, 255, 255, 0.98));
}

.profile-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.profile-item-top strong {
  font-size: var(--font-body);
  line-height: 1.35;
}

.profile-item-filename,
.profile-item-description,
.editor-hint,
.dialog-copy {
  margin: 0;
  color: var(--text-muted);
}

.profile-item-filename {
  font-size: var(--font-caption);
}

.profile-item-description {
  font-size: var(--font-caption);
  line-height: 1.5;
}

.profile-item-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: var(--text-subtle);
  font-size: var(--font-tiny);
}

.editor-header {
  padding: 14px 16px 12px;
  flex-shrink: 0;
}

.editor-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  min-height: 0;
  flex: 1;
  overflow-y: auto;
}

.field-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(220px, 1fr);
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.field span {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  font-weight: 700;
}

.editor-field {
  flex: 1;
  order: 2;
}

.yaml-editor {
  width: 100%;
  min-height: 360px;
  flex: 1;
  resize: none;
  box-sizing: border-box;
  padding: 14px 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  background: #fffdf9;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.65;
  font-family: Consolas, "SFMono-Regular", monospace;
  outline: none;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
}

.yaml-editor:focus {
  border-color: rgba(249, 115, 22, 0.72);
  box-shadow:
    0 0 0 3px rgba(249, 115, 22, 0.12),
    inset 0 1px 2px rgba(15, 23, 42, 0.04);
}

.copilot-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  order: 1;
  padding: 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  background: var(--surface-sunken);
}

.copilot-entry-label {
  display: block;
  margin-bottom: 4px;
  color: var(--brand-orange-soft);
  font-size: var(--font-tiny);
  font-weight: 800;
  text-transform: uppercase;
}

.copilot-entry p {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--font-caption);
  line-height: 1.5;
}

.summary-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 2px;
}

.summary-group + .summary-group,
.summary-actions {
  padding-top: 14px;
  border-top: 1px solid var(--border-subtle);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.summary-row span {
  color: var(--text-secondary);
  font-size: var(--font-caption);
}

.summary-row strong {
  color: var(--text-primary);
  font-size: var(--font-body);
  text-align: right;
  word-break: break-word;
}

.feedback {
  margin: 0;
  font-size: var(--font-caption);
  line-height: 1.6;
}

.feedback.success {
  color: var(--state-success);
}

.feedback.error {
  color: var(--state-danger);
}

.key-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.key-pill {
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(249, 115, 22, 0.12);
  color: var(--text-secondary);
  font-size: var(--font-tiny);
}

.summary-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dialog-card {
  width: min(480px, calc(100vw - 24px));
}

.copilot-dialog {
  width: min(720px, calc(100vw - 24px));
  max-height: calc(100vh - 48px);
}

.copilot-dialog :deep(.n-card__content) {
  min-height: 0;
  max-height: calc(100vh - 136px);
  overflow: hidden;
}

.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  margin-top: 48px;
}

@media (max-width: 1320px) {
  .config-page {
    grid-template-columns: minmax(260px, 300px) minmax(420px, 1fr) minmax(240px, 300px);
  }
}

@media (max-width: 1120px) {
  .config-page {
    grid-template-columns: minmax(260px, 320px) minmax(420px, 1fr);
    grid-template-rows: minmax(0, 1fr) auto;
    overflow-y: auto;
  }

  .summary-rail {
    grid-column: 1 / -1;
  }
}

@media (max-width: 860px) {
  .config-page {
    grid-template-columns: 1fr;
    overflow-y: auto;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }

  .copilot-entry {
    align-items: stretch;
    flex-direction: column;
  }

  .config-editor {
    min-height: 620px;
  }
}
</style>
