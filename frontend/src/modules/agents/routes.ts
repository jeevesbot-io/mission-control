import type { RouteRecordRaw } from 'vue-router'
import AgentsPage from './AgentsPage.vue'
import AgentDetailPage from './AgentDetailPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/agents',
    name: 'agents',
    component: AgentsPage,
    meta: { title: 'Agents' },
  },
  {
    path: '/agents/:agentId',
    name: 'agent-detail',
    component: AgentDetailPage,
    meta: { title: 'Agent Detail' },
  },
]

export default {
  module: {
    id: 'agents',
    name: 'Agents',
    icon: 'zap',
    navOrder: 2,
  },
  routes,
  overviewWidgets: [
    {
      id: 'agent-activity',
      component: () => import('./widgets/AgentActivity.vue'),
    },
  ],
}
