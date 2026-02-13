import type { RouteRecordRaw } from 'vue-router'
import OverviewPage from './OverviewPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'overview',
    component: OverviewPage,
    meta: { title: 'Overview' },
  },
]

export default {
  module: {
    id: 'overview',
    name: 'Overview',
    icon: '🏠',
    navOrder: 0,
  },
  routes,
}
