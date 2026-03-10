import type { RouteRecordRaw } from 'vue-router'
import SkillsPage from './SkillsPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/skills',
    name: 'skills',
    component: SkillsPage,
    meta: { title: 'Skills Browser' },
  },
]

export default {
  module: {
    id: 'skills',
    name: 'Skills',
    icon: 'sparkles',
    navOrder: 6,
  },
  routes,
}
