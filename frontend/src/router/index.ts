import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

interface ModuleRegistration {
  module: { id: string; name: string; icon: string; navOrder: number }
  routes: RouteRecordRaw[]
}

// Auto-discover modules that export a default registration
const moduleFiles = import.meta.glob<{ default: ModuleRegistration }>(
  '../modules/*/routes.ts',
  { eager: true },
)

const moduleRegistry: ModuleRegistration['module'][] = []
const moduleRoutes: RouteRecordRaw[] = []

for (const [, mod] of Object.entries(moduleFiles).sort(([a], [b]) => a.localeCompare(b))) {
  const registration = mod?.default
  if (registration?.module && registration?.routes) {
    moduleRegistry.push(registration.module)
    moduleRoutes.push(...registration.routes)
  }
}

// Sort by navOrder
moduleRegistry.sort((a, b) => a.navOrder - b.navOrder)

const router = createRouter({
  history: createWebHistory(),
  routes: moduleRoutes,
})

export { moduleRegistry }
export default router
