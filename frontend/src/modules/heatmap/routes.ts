import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/activity',
    name: 'activity',
    component: () => import('./HeatmapPage.vue'),
    meta: { title: 'Activity' },
  },
]

export default {
  module: {
    id: 'heatmap',
    name: 'Activity',
    icon: 'flame',
    navOrder: 4,
  },
  routes,
}
