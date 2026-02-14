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
    icon: 'message-circle',
    navOrder: 4,
  },
  routes,
}
