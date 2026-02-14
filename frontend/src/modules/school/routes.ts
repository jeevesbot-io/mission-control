import type { RouteRecordRaw } from 'vue-router'
import SchoolPage from './SchoolPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/school',
    name: 'school',
    component: SchoolPage,
    meta: { title: 'School' },
  },
]

export default {
  module: {
    id: 'school',
    name: 'School',
    icon: 'graduation-cap',
    navOrder: 3,
  },
  routes,
  overviewWidgets: [
    {
      id: 'today-events',
      component: () => import('./widgets/TodayEvents.vue'),
    },
  ],
}
