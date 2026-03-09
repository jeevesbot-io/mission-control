import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/heatmap',
    name: 'heatmap',
    component: () => import('./HeatmapPage.vue'),
    meta: { title: 'Heatmap' },
  },
]

export default {
  module: {
    id: 'heatmap',
    name: 'Heatmap',
    icon: 'flame',
    navOrder: 4,
  },
  routes,
}
