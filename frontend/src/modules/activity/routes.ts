import type { RouteRecordRaw } from 'vue-router'
import ActivityPage from './ActivityPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/activity',
    name: 'activity',
    component: ActivityPage,
    meta: { title: 'Activity Timeline' },
  },
]

export default {
  module: {
    id: 'activity',
    name: 'Activity',
    icon: 'activity',
    navOrder: 8,
  },
  routes,
  overviewWidgets: [
    {
      id: 'recent-activity',
      component: () => import('./widgets/RecentActivity.vue'),
    },
  ],
}
