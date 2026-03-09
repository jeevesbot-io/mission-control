import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('./TasksPage.vue'),
    meta: { title: 'Tasks' },
    children: [
      {
        path: ':id',
        name: 'task-detail',
        component: () => import('./TasksPage.vue'),
        meta: { title: 'Task Detail' },
      },
    ],
  },
]

export default {
  module: {
    id: 'tasks',
    name: 'Tasks',
    icon: 'check-square',
    navOrder: 3,
  },
  routes,
  overviewWidgets: [
    {
      id: 'tasks-summary',
      component: () => import('./widgets/TasksSummary.vue'),
    },
  ],
}
