import type { RouteRecordRaw } from 'vue-router'
import MemoryPage from './MemoryPage.vue'
import DailyMemoryPage from './DailyMemoryPage.vue'
import LongTermPage from './LongTermPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/memory',
    name: 'memory',
    component: MemoryPage,
    meta: { title: 'Memory' },
  },
  {
    path: '/memory/daily/:date',
    name: 'memory-daily',
    component: DailyMemoryPage,
    meta: { title: 'Daily Memory' },
  },
  {
    path: '/memory/long-term',
    name: 'memory-long-term',
    component: LongTermPage,
    meta: { title: 'Long-Term Memory' },
  },
]

export default {
  module: {
    id: 'memory',
    name: 'Memory',
    icon: '\u{1F4DC}',
    navOrder: 1,
  },
  routes,
  overviewWidgets: [
    {
      id: 'recent-memories',
      component: () => import('./widgets/RecentMemories.vue'),
    },
  ],
}
