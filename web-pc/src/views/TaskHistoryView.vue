<template>
  <div class="tool-page">
    <section class="tool-shell">
      <div class="page-header">
        <div>
          <p class="eyebrow">History</p>
          <h2>任务历史</h2>
          <p>近期解析任务、处理状态与产物入口将在这里集中展示。</p>
        </div>
        <div class="header-actions">
          <n-button size="small" quaternary :loading="loading" @click="refresh">
            刷新
          </n-button>
        </div>
      </div>

      <n-spin :show="loading">
        <!-- Desktop Table -->
        <div v-if="!isMobile" class="table-shell">
          <div class="table-row table-head">
            <span class="col-id">任务ID</span>
            <span class="col-source">文档来源</span>
            <span class="col-status">状态</span>
            <span class="col-stage">阶段</span>
            <span class="col-progress">进度</span>
            <span class="col-time">更新时间</span>
            <span class="col-actions">操作</span>
          </div>

          <template v-if="tasks.length">
            <div
              v-for="item in tasks"
              :key="item.task_id"
              class="table-row table-body"
              :class="{ 'row-deleting': deletingId === item.task_id }"
            >
              <span class="col-id" :title="item.task_id">
                <code>{{ item.task_id.slice(0, 8) }}</code>
              </span>
              <span class="col-source" :title="item.document_url">
                {{ truncateUrl(item.document_url) }}
              </span>
              <span class="col-status">
                <n-tag size="small" round :type="statusType(item.status)">
                  {{ statusLabel(item.status) }}
                </n-tag>
              </span>
              <span class="col-stage">{{ stageLabel(item.stage) }}</span>
              <span class="col-progress">
                <n-progress
                  type="line"
                  :percentage="item.overall_progress"
                  :height="6"
                  :show-indicator="false"
                  :status="item.status === 'failed' ? 'error' : 'success'"
                />
              </span>
              <span class="col-time">{{ formatTime(item.updated_at) }}</span>
              <span class="col-actions">
                <n-button-group size="tiny">
                  <n-button quaternary @click="viewTask(item.task_id)">查看</n-button>
                  <n-button
                    quaternary
                    :disabled="item.status !== 'completed'"
                    @click="downloadTask(item.task_id)"
                  >
                    下载
                  </n-button>
                  <n-button quaternary type="error" @click="confirmDelete(item)">删除</n-button>
                </n-button-group>
              </span>
            </div>
          </template>

          <div v-else class="empty-row">暂无任务记录</div>
        </div>

        <!-- Mobile Cards -->
        <div v-else class="card-list">
          <div
            v-for="item in tasks"
            :key="item.task_id"
            class="task-card"
            :class="{ 'card-deleting': deletingId === item.task_id }"
          >
            <div class="card-header">
              <code class="card-id">{{ item.task_id.slice(0, 8) }}</code>
              <n-tag size="small" round :type="statusType(item.status)">
                {{ statusLabel(item.status) }}
              </n-tag>
            </div>
            <p class="card-source" :title="item.document_url">
              {{ truncateUrl(item.document_url, 40) }}
            </p>
            <div class="card-meta">
              <span>{{ stageLabel(item.stage) }}</span>
              <span>{{ formatTime(item.updated_at) }}</span>
            </div>
            <n-progress
              type="line"
              :percentage="item.overall_progress"
              :height="6"
              :show-indicator="true"
              :status="item.status === 'failed' ? 'error' : 'success'"
            />
            <div class="card-actions">
              <n-button size="small" quaternary @click="viewTask(item.task_id)">查看</n-button>
              <n-button
                size="small"
                quaternary
                :disabled="item.status !== 'completed'"
                @click="downloadTask(item.task_id)"
              >
                下载
              </n-button>
              <n-button size="small" quaternary type="error" @click="confirmDelete(item)">
                删除
              </n-button>
            </div>
          </div>

          <div v-if="!tasks.length" class="empty-row">暂无任务记录</div>
        </div>
      </n-spin>

      <!-- Pagination -->
      <div v-if="total > 0" class="pagination-bar">
        <n-pagination
          v-model:page="page"
          v-model:page-size="pageSize"
          :item-count="total"
          :page-sizes="[10, 20, 50]"
          show-size-picker
          show-quick-jumper
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NButtonGroup,
  NPagination,
  NProgress,
  NSpin,
  NTag,
  useDialog,
  useMessage,
} from 'naive-ui'
import { listTasks, deleteTask, getTaskDownloadUrl } from '@/api/taskApi'
import type { TaskListItem, TaskStatus } from '@/types/task'

const router = useRouter()
const dialog = useDialog()
const message = useMessage()

const loading = ref(false)
const tasks = ref<TaskListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const offset = computed(() => (page.value - 1) * pageSize.value)
const deletingId = ref<string | null>(null)

const isMobile = ref(window.innerWidth < 960)
window.addEventListener('resize', () => {
  isMobile.value = window.innerWidth < 960
})

function statusType(status: TaskStatus) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'processing':
      return 'info'
    case 'failed':
      return 'error'
    default:
      return 'default'
  }
}

function statusLabel(status: TaskStatus) {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] ?? status
}

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    pending: '等待中',
    mineru: '文档解析',
    extraction: '实体提取',
    highlight: '高亮渲染',
    completed: '已完成',
    failed: '处理失败',
  }
  return map[stage] ?? stage
}

function truncateUrl(url: string, max = 28) {
  if (!url) return '-'
  return url.length > max ? url.slice(0, max) + '…' : url
}

function formatTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function fetchTasks() {
  loading.value = true
  try {
    const res = await listTasks(pageSize.value, offset.value)
    tasks.value = res.tasks
    total.value = res.total
  } catch (error) {
    console.error('Fetch task list failed:', error)
    message.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

function refresh() {
  fetchTasks()
}

function handlePageChange() {
  fetchTasks()
}

function handlePageSizeChange() {
  page.value = 1
  fetchTasks()
}

function viewTask(taskId: string) {
  router.push({ path: '/', query: { task_id: taskId } })
}

function downloadTask(taskId: string) {
  window.open(getTaskDownloadUrl(taskId), '_blank', 'noopener,noreferrer')
}

function confirmDelete(item: TaskListItem) {
  dialog.warning({
    title: '删除确认',
    content: `确定要删除任务 ${item.task_id.slice(0, 8)} 吗？该操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      deletingId.value = item.task_id
      try {
        await deleteTask(item.task_id)
        message.success('任务已删除')
        await fetchTasks()
      } catch (error) {
        console.error('Delete task failed:', error)
        message.error('删除任务失败')
      } finally {
        deletingId.value = null
      }
    },
  })
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.tool-page {
  flex: 1;
  padding: 12px;
  overflow: auto;
}

.tool-shell {
  min-height: 360px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-rail);
  box-shadow: var(--shadow-sm);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.eyebrow {
  margin-bottom: 4px;
  color: var(--brand-orange-soft);
  font-size: var(--font-tiny);
  font-weight: 800;
  text-transform: uppercase;
}

h2 {
  margin-bottom: 8px;
  color: var(--text-primary);
  font-size: var(--font-display);
}

.page-header p {
  margin: 0;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.table-shell {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-sunken);
}

.table-row {
  display: grid;
  grid-template-columns: 100px 1fr 100px 100px 120px 120px 160px;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
}

.table-head {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  font-weight: 800;
  background: rgba(241, 245, 249, 0.74);
  border-bottom: 1px solid var(--border-subtle);
}

.table-body {
  color: var(--text-primary);
  font-size: var(--font-body);
  border-bottom: 1px solid var(--border-subtle);
  transition: background-color var(--transition-fast);
}

.table-body:last-child {
  border-bottom: none;
}

.table-body:hover {
  background: rgba(255, 247, 237, 0.6);
}

.table-body.row-deleting {
  opacity: 0.5;
  pointer-events: none;
}

.col-id code {
  font-family: Consolas, 'SFMono-Regular', monospace;
  font-size: var(--font-caption);
  color: var(--text-secondary);
}

.col-source {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
  font-size: var(--font-caption);
}

.col-progress {
  min-width: 0;
}

.col-time {
  color: var(--text-subtle);
  font-size: var(--font-caption);
  white-space: nowrap;
}

.empty-row {
  padding: 40px 12px;
  color: var(--text-subtle);
  font-size: var(--font-body);
  text-align: center;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

/* Mobile Cards */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-sunken);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-card.card-deleting {
  opacity: 0.5;
  pointer-events: none;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-id {
  font-family: Consolas, 'SFMono-Regular', monospace;
  font-size: var(--font-caption);
  color: var(--text-secondary);
}

.card-source {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--font-caption);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: var(--text-subtle);
  font-size: var(--font-tiny);
}

.card-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid var(--border-subtle);
}
</style>
