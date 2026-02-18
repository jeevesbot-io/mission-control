import type { RouteRecordRaw } from 'vue-router'
import ContentPage from './ContentPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/content',
    name: 'content',
    component: ContentPage,
    meta: { title: 'Content Pipeline' },
  },
]

export default {
  module: {
    id: 'content',
    name: 'Content Pipeline',
    icon: 'video',
    navOrder: 7,
  },
  routes,
}
