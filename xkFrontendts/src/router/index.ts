import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'scheduler',
      component: () => import('../views/CourseScheduler.vue'),
    },
    {
      path: '/sync',
      name: 'sync',
      component: () => import('../views/Diagnose.vue'),
    },
  ],
})

export default router
