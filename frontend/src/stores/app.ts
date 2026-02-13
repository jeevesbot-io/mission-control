import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

function readBoolean(key: string, fallback: boolean): boolean {
  const stored = localStorage.getItem(key)
  if (stored === null) return fallback
  return stored === 'true'
}

export const useAppStore = defineStore('app', () => {
  const darkMode = ref(readBoolean('mc-dark-mode', true))
  const sidebarCollapsed = ref(readBoolean('mc-sidebar-collapsed', false))
  const user = ref<{ id: string; name: string } | null>(null)

  watch(darkMode, (v) => localStorage.setItem('mc-dark-mode', String(v)))
  watch(sidebarCollapsed, (v) => localStorage.setItem('mc-sidebar-collapsed', String(v)))

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { darkMode, sidebarCollapsed, user, toggleDarkMode, toggleSidebar }
})
