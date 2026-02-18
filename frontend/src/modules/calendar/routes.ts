import type { RouteRecordRaw } from 'vue-router'
import CalendarPage from './CalendarPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/calendar',
    name: 'calendar',
    component: CalendarPage,
    meta: { title: 'Calendar' },
  },
]

export default {
  module: {
    id: 'calendar',
    name: 'Calendar',
    icon: 'calendar',
    navOrder: 6,
  },
  routes,
}
