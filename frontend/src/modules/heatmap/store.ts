import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useApi } from '@/composables/useApi'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentCount {
  agent_id: string
  count: number
}

export interface HeatmapDay {
  date: string
  count: number
  agents: AgentCount[]
}

export interface AgentRun {
  id: string
  agent_id: string
  trigger: string
  outcome: string
  duration_ms: number
  channel: string
  prompt_preview: string
  created_at: string
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useHeatmapStore = defineStore('heatmap', () => {
  const api = useApi()

  // Data
  const heatmapData = ref<HeatmapDay[]>([])
  const dayRuns = ref<AgentRun[]>([])

  // UI state
  const year = ref(new Date().getFullYear())
  const selectedDate = ref<string | null>(null)
  const agentFilter = ref<string | null>(null)
  const loading = ref(false)
  const dayLoading = ref(false)
  const error = ref<string | null>(null)

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------

  /** All unique agents across the heatmap data */
  const agents = computed(() => {
    const set = new Set<string>()
    for (const day of heatmapData.value) {
      for (const a of day.agents) {
        set.add(a.agent_id)
      }
    }
    return Array.from(set).sort()
  })

  /** Heatmap data as a map: date → HeatmapDay for fast lookup */
  const heatmapMap = computed(() => {
    const map = new Map<string, HeatmapDay>()
    for (const day of heatmapData.value) {
      map.set(day.date, day)
    }
    return map
  })

  /** Filtered day runs by agent */
  const filteredDayRuns = computed(() => {
    if (!agentFilter.value) return dayRuns.value
    return dayRuns.value.filter((r) => r.agent_id === agentFilter.value)
  })

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  async function fetchHeatmap() {
    loading.value = true
    error.value = null
    try {
      heatmapData.value = await api.get<HeatmapDay[]>(
        `/api/runs/heatmap?year=${year.value}`,
      )
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load heatmap data'
    } finally {
      loading.value = false
    }
  }

  async function fetchDayRuns(date: string, agentId?: string | null) {
    dayLoading.value = true
    try {
      const params = new URLSearchParams({ date })
      if (agentId) params.set('agent_id', agentId)
      dayRuns.value = await api.get<AgentRun[]>(`/api/runs/day?${params}`)
    } catch {
      dayRuns.value = []
    } finally {
      dayLoading.value = false
    }
  }

  async function selectDate(date: string | null) {
    selectedDate.value = date
    if (date) {
      await fetchDayRuns(date, agentFilter.value)
    } else {
      dayRuns.value = []
    }
  }

  async function setYear(y: number) {
    year.value = y
    selectedDate.value = null
    dayRuns.value = []
    await fetchHeatmap()
  }

  async function setAgentFilter(agent: string | null) {
    agentFilter.value = agent
    if (selectedDate.value) {
      await fetchDayRuns(selectedDate.value, agent)
    }
  }

  // ---------------------------------------------------------------------------
  // Return
  // ---------------------------------------------------------------------------

  return {
    // Data
    heatmapData,
    dayRuns,
    // UI
    year,
    selectedDate,
    agentFilter,
    loading,
    dayLoading,
    error,
    // Computed
    agents,
    heatmapMap,
    filteredDayRuns,
    // Actions
    fetchHeatmap,
    fetchDayRuns,
    selectDate,
    setYear,
    setAgentFilter,
  }
})
