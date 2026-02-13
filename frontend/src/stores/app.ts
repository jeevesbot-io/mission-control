import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const darkMode = ref(true)
  const sidebarCollapsed = ref(false)
  const user = ref<{ id: string; name: string } | null>(null)

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { darkMode, sidebarCollapsed, user, toggleDarkMode, toggleSidebar }
})
