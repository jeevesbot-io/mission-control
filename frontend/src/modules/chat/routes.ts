import type { RouteRecordRaw } from 'vue-router'
import ChatPage from './ChatPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/chat',
    name: 'chat',
    component: ChatPage,
    meta: { title: 'Chat' },
  },
]

export default {
  module: {
    id: 'chat',
    name: 'Chat',
    icon: '\u{1F4AC}',
    navOrder: 4,
  },
  routes,
}
