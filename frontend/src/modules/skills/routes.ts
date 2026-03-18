import type { RouteRecordRaw } from 'vue-router'
import SkillsPage from './SkillsPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/skills',
    name: 'skills',
    component: SkillsPage,
    meta: { title: 'Skills Hub' },
  },
]

export default {
  module: {
    id: 'skills',
    name: 'Skills Hub',
    icon: 'sparkles',
    navOrder: 6,
  },
  routes,
}
