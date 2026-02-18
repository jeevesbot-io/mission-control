import type { RouteRecordRaw } from 'vue-router'
import WarRoomPage from './WarRoomPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/warroom',
    name: 'warroom',
    component: WarRoomPage,
    meta: { title: 'War Room' },
  },
]

export default {
  module: {
    id: 'warroom',
    name: 'War Room',
    icon: 'swords',
    navOrder: 5,
  },
  routes,
  overviewWidgets: [
    {
      id: 'warroom-summary',
      component: () => import('./widgets/WarRoomSummary.vue'),
    },
  ],
}
