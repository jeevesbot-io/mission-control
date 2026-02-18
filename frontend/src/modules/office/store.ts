import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { components } from '@/types/api'

type AgentWorkstation = components['schemas']['AgentWorkstation']

export const useOfficeStore = defineStore('office', () => {
  const workstations = ref<AgentWorkstation[]>([])
  const stats = ref<Record<string, any>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchOffice() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/office/')
      if (!response.ok) {
        throw new Error(`Failed to fetch office: ${response.statusText}`)
      }
      const data = await response.json()
      workstations.value = data.workstations || []
      stats.value = data.office_stats || {}
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error fetching office:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    workstations,
    stats,
    loading,
    error,
    fetchOffice,
  }
})
