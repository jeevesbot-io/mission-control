import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import type { components } from '@/types/api'

type AgentWorkstation = components['schemas']['AgentWorkstation']

export const useOfficeStore = defineStore('office', () => {
  const api = useApi()
  const workstations = ref<AgentWorkstation[]>([])
  const stats = ref<Record<string, any>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchOffice() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ workstations: AgentWorkstation[]; office_stats: Record<string, any> }>('/api/office/')
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
