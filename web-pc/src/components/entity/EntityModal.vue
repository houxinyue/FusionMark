<template>
  <n-modal :show="visible" title="文本实体回溯" preset="card" style="width: 800px" @update:show="emit('update:visible', $event)">
    <div v-if="entities && entities.length > 0" class="entity-tags">
      <div
        v-for="(entity, index) in entities"
        :key="index"
        class="entity-tag"
        :style="getTagStyle(entity.type)"
        :title="entity.text"
      >
        <span class="tag-dot" :style="getDotStyle(entity.type)" />
        <span class="tag-label">{{ getLabel(entity.type) }}</span>
        <span class="tag-text">{{ entity.text }}</span>
      </div>
    </div>

    <iframe v-if="htmlContent" :srcdoc="htmlContent" class="entity-html-frame" sandbox="allow-same-origin"></iframe>
    <div v-else class="empty-state">暂无提取结果</div>
  </n-modal>
</template>

<script setup lang="ts">
import { NModal } from 'naive-ui'
import type { ExtractedEntity } from '@/types/entity'
import { ENTITY_COLORS } from '@/constants/entityColors'

defineProps<{
  visible: boolean
  htmlContent?: string
  entities?: ExtractedEntity[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

function getTagStyle(type: string) {
  const config = ENTITY_COLORS[type]
  if (!config) return {}
  return {
    backgroundColor: config.bg,
    color: config.text,
  }
}

function getDotStyle(type: string) {
  const config = ENTITY_COLORS[type]
  if (!config) return {}
  return {
    backgroundColor: config.text,
  }
}

function getLabel(type: string) {
  return ENTITY_COLORS[type]?.label ?? type
}
</script>

<style scoped>
.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
}

.entity-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-lg);
  font-size: var(--font-caption);
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.24);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
  user-select: none;
  max-width: 200px;
}

.entity-tag:hover {
  transform: translateY(-2px);
  filter: saturate(1.04);
  box-shadow:
    0 8px 20px rgba(0, 0, 0, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

.tag-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-label {
  font-weight: 600;
  flex-shrink: 0;
}

.tag-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.entity-html-frame {
  width: 100%;
  height: 500px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: white;
}

.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--text-muted);
  font-size: var(--font-body);
}
</style>
