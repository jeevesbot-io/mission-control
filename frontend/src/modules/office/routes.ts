import type { RouteRecordRaw } from 'vue-router'
import OfficePage from './OfficePage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/office',
    name: 'office',
    component: OfficePage,
    meta: { title: 'Office View' },
  },
]

export default {
  module: {
    id: 'office',
    name: 'Office View',
    icon: 'building',
    navOrder: 8,
  },
  routes,
}
