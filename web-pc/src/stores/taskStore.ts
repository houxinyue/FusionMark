import { defineStore } from 'pinia'
import type { TaskProgress, TaskStatus } from '@/types/task'

export const useTaskStore = defineStore('task', {
  state: () => ({
    currentTaskId: null as string | null,
    status: 'pending' as TaskStatus,
    progress: null as TaskProgress | null,
    isProcessing: false,
    logs: [] as string[],
    entityArtifactUrl: null as string | null,
  }),

  actions: {
    setTaskId(taskId: string) {
      this.currentTaskId = taskId
    },

    reset() {
      this.currentTaskId = null
      this.status = 'pending'
      this.progress = null
      this.isProcessing = false
      this.logs = []
      this.entityArtifactUrl = null
    },
  },
})
