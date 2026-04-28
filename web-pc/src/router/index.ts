import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'ProcessPdf',
      component: () => import('@/views/ProcessPdfView.vue'),
    },
    {
      path: '/history',
      name: 'TaskHistory',
      component: () => import('@/views/TaskHistoryView.vue'),
    },
    {
      path: '/config',
      name: 'Config',
      component: () => import('@/views/ConfigView.vue'),
    },
  ],
})
