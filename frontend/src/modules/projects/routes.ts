import type { RouteRecordRaw } from 'vue-router'

const ProjectsPage = () => import('./ProjectsPage.vue')
const ProjectDetailPage = () => import('./ProjectDetailPage.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/projects',
    name: 'projects',
    component: ProjectsPage,
    meta: { title: 'Projects' },
  },
  {
    path: '/projects/:id',
    name: 'project-detail',
    component: ProjectDetailPage,
    meta: { title: 'Project Detail' },
  },
]

export default {
  module: {
    id: 'projects',
    name: 'Projects',
    icon: 'folder-kanban',
    navOrder: 4,
  },
  routes,
}
