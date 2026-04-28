import { defineStore } from 'pinia'
import type {
  StageName,
  StageProgress,
  TaskDetail,
  TaskProgress,
  TaskResult,
  TaskSnapshot,
  TaskStatus,
} from '@/types/task'

const stageKeys: StageName[] = ['mineru', 'extraction', 'highlight']

function createDefaultStage(): StageProgress {
  return {
    state: 'pending',
    progress: 0,
    logs: [],
  }
}

function normalizeStage(stage?: Partial<StageProgress>): StageProgress {
  return {
    state: stage?.state ?? 'pending',
    progress: typeof stage?.progress === 'number' ? stage.progress : 0,
    logs: Array.isArray(stage?.logs) ? stage.logs : [],
  }
}

function createDefaultProgress(): TaskProgress {
  return {
    stage: 'pending',
    stage_progress: 0,
    overall_progress: 0,
    mineru: createDefaultStage(),
    extraction: createDefaultStage(),
    highlight: createDefaultStage(),
  }
}

function normalizeProgress(snapshot: TaskSnapshot | TaskDetail): TaskProgress {
  const source = ('progress' in snapshot && snapshot.progress ? snapshot.progress : snapshot) as
    Partial<TaskProgress> & TaskSnapshot
  const base = createDefaultProgress()

  return {
    stage: source.stage ?? base.stage,
    stage_progress:
      typeof source.stage_progress === 'number' ? source.stage_progress : base.stage_progress,
    overall_progress:
      typeof source.overall_progress === 'number' ? source.overall_progress : base.overall_progress,
    mineru: normalizeStage(source.mineru),
    extraction: normalizeStage(source.extraction),
    highlight: normalizeStage(source.highlight),
  }
}

function extractLogs(progress: TaskProgress) {
  return stageKeys.flatMap((stage) =>
    progress[stage].logs.map((text) => ({
      key: `${stage}:${text}`,
      text,
    })),
  )
}

export const useTaskStore = defineStore('task', {
  state: () => ({
    currentTaskId: null as string | null,
    status: 'pending' as TaskStatus,
    progress: null as TaskProgress | null,
    isProcessing: false,
    logs: [] as string[],
    logKeys: new Set<string>(),
    entityArtifactUrl: null as string | null,
    result: null as TaskResult | null,
    message: '' as string,
  }),

  actions: {
    setTaskId(taskId: string) {
      this.currentTaskId = taskId
    },

    startTask(taskId: string) {
      this.currentTaskId = taskId
      this.status = 'pending'
      this.progress = null
      this.isProcessing = true
      this.logs = []
      this.logKeys = new Set<string>()
      this.entityArtifactUrl = null
      this.result = null
      this.message = '任务已提交，等待后端开始处理'
    },

    applyTaskSnapshot(snapshot: TaskSnapshot | TaskDetail) {
      if (snapshot.task_id) {
        this.currentTaskId = snapshot.task_id
      }

      if (snapshot.status) {
        this.status = snapshot.status
      }

      this.progress = normalizeProgress(snapshot)
      this.message = snapshot.message ?? this.message
      this.result = snapshot.result || this.result
      this.isProcessing = this.status === 'pending' || this.status === 'processing'
      this.appendStageLogs(this.progress)
    },

    appendStageLogs(progress: TaskProgress) {
      for (const log of extractLogs(progress)) {
        if (!this.logKeys.has(log.key)) {
          this.logKeys.add(log.key)
          this.logs.push(log.text)
        }
      }
    },

    failTask(message?: string) {
      this.status = 'failed'
      this.isProcessing = false
      this.message = message ?? '任务处理失败'
    },

    reset() {
      this.currentTaskId = null
      this.status = 'pending'
      this.progress = null
      this.isProcessing = false
      this.logs = []
      this.logKeys = new Set<string>()
      this.entityArtifactUrl = null
      this.result = null
      this.message = ''
    },
  },
})
