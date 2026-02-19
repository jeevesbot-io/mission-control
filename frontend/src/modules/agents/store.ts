import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

interface AgentInfo {
  agent_id: string
  last_activity: string | null
  last_message: string | null
  last_level: string | null
  total_entries: number
  warning_count: number
}

interface AgentLogEntry {
  id: number
  agent_id: string
  level: string
  message: string
  metadata: Record<string, unknown> | null
  created_at: string
}

interface AgentStats {
  total_entries: number
  unique_agents: number
  entries_24h: number
  warning_count: number
  health_rate: number
}

interface CronJob {
  agent_id: string
  schedule: string
  enabled: boolean
  last_run: string | null
  next_run: string | null
}

interface ActivityEvent {
  event: string
  agent_id: string
  message: string
  timestamp?: string
}

export type { AgentInfo, AgentLogEntry, AgentStats, CronJob, ActivityEvent }

export const useAgentsStore = defineStore('agents', () => {
  const api = useApi()

  const agents = ref<AgentInfo[]>([])
  const stats = ref<AgentStats | null>(null)
  const cronJobs = ref<CronJob[]>([])
  const logEntries = ref<AgentLogEntry[]>([])
  const logTotal = ref(0)
  const activityFeed = ref<ActivityEvent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAgents() {
    loading.value = true
    error.value = null
    try {
      agents.value = await api.get<AgentInfo[]>('/api/agents/')
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load agents'
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      stats.value = await api.get<AgentStats>('/api/agents/stats')
    } catch {
      stats.value = null
    }
  }

  async function fetchCron() {
    try {
      const data = await api.get<{ jobs: CronJob[] }>('/api/agents/cron')
      cronJobs.value = data.jobs
    } catch {
      cronJobs.value = []
    }
  }

  async function fetchLog(agentId: string, page = 1, level?: string) {
    loading.value = true
    try {
      const params = new URLSearchParams({ page: String(page) })
      if (level) params.set('level', level)
      const data = await api.get<{ entries: AgentLogEntry[]; total: number }>(
        `/api/agents/${agentId}/log?${params}`
      )
      logEntries.value = data.entries
      logTotal.value = data.total
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load log'
    } finally {
      loading.value = false
    }
  }

  async function triggerAgent(agentId: string): Promise<boolean> {
    try {
      await api.post<{ success: boolean }>(`/api/agents/${agentId}/trigger`)
      return true
    } catch {
      return false
    }
  }

  function addActivity(event: ActivityEvent) {
    event.timestamp = new Date().toISOString()
    activityFeed.value.unshift(event)
    if (activityFeed.value.length > 50) activityFeed.value.pop()
  }

  return {
    agents,
    stats,
    cronJobs,
    logEntries,
    logTotal,
    activityFeed,
    loading,
    error,
    fetchAgents,
    fetchStats,
    fetchCron,
    fetchLog,
    triggerAgent,
    addActivity,
  }
})
