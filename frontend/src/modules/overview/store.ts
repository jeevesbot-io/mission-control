import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export interface OverviewStats {
  agents_active: number
  events_this_week: number
  emails_processed: number
  tasks_pending: number
}

export interface AgentStatusSummary {
  total_entries: number
  info_count: number
  warning_count: number
  entries_24h: number
  unique_agents: number
  health_rate: number
}

export interface UpcomingEvent {
  id: number
  child: string
  summary: string
  event_date: string
  event_end_date: string | null
  event_time: string | null
  days_away: number
}

export interface RecentActivity {
  id: string
  agent_id: string
  level: string
  message: string
  created_at: string
}

export interface SystemHealth {
  status: string
  database: boolean
  uptime_seconds: number
  version: string
}

export interface OverviewData {
  stats: OverviewStats
  agent_summary: AgentStatusSummary
  upcoming_events: UpcomingEvent[]
  recent_activity: RecentActivity[]
  health: SystemHealth
}

export const useOverviewStore = defineStore('overview', () => {
  const api = useApi()

  const data = ref<OverviewData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchOverview() {
    loading.value = true
    error.value = null
    try {
      data.value = await api.get<OverviewData>('/api/overview/')
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load overview'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetchOverview }
})
