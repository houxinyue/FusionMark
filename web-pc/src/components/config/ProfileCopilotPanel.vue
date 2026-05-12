<template>
  <section class="copilot-panel">
    <div class="panel-header">
      <div>
        <p class="rail-kicker">Copilot</p>
        <h3>配置草稿</h3>
      </div>
      <n-tag v-if="copilot.validation.valid" size="small" type="success">校验通过</n-tag>
      <n-tag v-else-if="copilot.draftYaml" size="small" type="warning">待修正</n-tag>
    </div>

    <div class="message-list">
      <div
        v-for="message in copilot.messages.slice(-4)"
        :key="`${message.created_at}-${message.role}`"
        class="message-item"
        :class="message.role"
      >
        <span>{{ message.role === 'user' ? '你' : '助手' }}</span>
        <p>{{ message.content }}</p>
      </div>
      <p v-if="!copilot.messages.length" class="empty-copy">
        描述文档类型、抽取类别、颜色或 OCR/Table 需求。
      </p>
    </div>

    <n-input
      v-model:value="prompt"
      type="textarea"
      placeholder="例如：帮我生成一个财务年报高亮配置，抽取公司、收入、利润、同比变化和风险提示"
      :autosize="{ minRows: 3, maxRows: 5 }"
      :disabled="copilot.loading"
      @keydown.ctrl.enter.prevent="submitPrompt"
    />

    <div class="panel-actions">
      <n-button size="small" type="primary" :loading="copilot.loading" @click="submitPrompt">
        生成草稿
      </n-button>
      <n-button size="small" :disabled="!copilot.draftYaml" :loading="copilot.validating" @click="validateDraft">
        重新校验
      </n-button>
      <n-button size="small" :disabled="!copilot.canApply" @click="applyDraft">
        应用到编辑器
      </n-button>
    </div>

    <p v-if="copilot.errorMessage" class="feedback error">{{ copilot.errorMessage }}</p>
    <p v-else-if="copilot.rejected" class="feedback warning">请求已被限制在 Profile 配置范围内。</p>
    <div v-if="copilot.validation.errors.length" class="validation-errors">
      <p v-for="error in copilot.validation.errors" :key="error">{{ error }}</p>
    </div>

    <div v-if="copilot.referencedProfiles.length" class="reference-list">
      <span>参考 Profile</span>
      <n-tag
        v-for="profile in copilot.referencedProfiles"
        :key="profile.profile_id"
        size="small"
        round
      >
        {{ profile.display_name }}
      </n-tag>
    </div>

    <pre v-if="copilot.draftYaml" class="draft-preview">{{ copilot.draftYaml }}</pre>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NButton, NInput, NTag } from 'naive-ui'
import { useProfileCopilotStore } from '@/stores/profileCopilotStore'

const emit = defineEmits<{
  applyDraft: [draftYaml: string]
}>()

const copilot = useProfileCopilotStore()
const prompt = ref('')

async function submitPrompt() {
  if (!prompt.value.trim()) return
  await copilot.sendMessage(prompt.value)
  prompt.value = ''
}

async function validateDraft() {
  await copilot.validateDraft()
}

function applyDraft() {
  if (!copilot.canApply) return
  emit('applyDraft', copilot.draftYaml)
}
</script>

<style scoped>
.copilot-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  max-height: calc(100vh - 160px);
  overflow: hidden;
}

.panel-header,
.panel-actions,
.reference-list {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.panel-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-title);
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
}

.message-item {
  padding: 8px;
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  background: var(--surface-sunken);
}

.message-item.user {
  border-color: rgba(37, 99, 235, 0.22);
}

.message-item span,
.reference-list span {
  color: var(--text-muted);
  font-size: var(--font-tiny);
  font-weight: 800;
}

.message-item p,
.empty-copy,
.feedback,
.validation-errors p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: var(--font-small);
  line-height: 1.5;
}

.feedback.error,
.validation-errors p {
  color: var(--state-danger);
}

.feedback.warning {
  color: var(--state-warning);
}

.draft-preview {
  max-height: min(340px, 36vh);
  margin: 0;
  padding: 10px;
  overflow: auto;
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  background: var(--surface-sunken);
  color: var(--text-primary);
  font-size: var(--font-small);
  line-height: 1.5;
  white-space: pre-wrap;
}

@media (max-width: 720px) {
  .panel-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .panel-actions :deep(.n-button) {
    width: 100%;
  }
}
</style>
