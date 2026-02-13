import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

interface AgentInfo {
  agent_id: string
  last_run: string | null
  last_status: string | null
  total_runs: number
}

interface AgentRun {
  id: string
  agent_id: string
  run_type: string
  trigger: string
  status: string
  summary: string | null
  duration_ms: number | null
  tokens_used: number | null
  created_at: string
}

interface AgentRunsPage {
  runs: AgentRun[]
  total: number
  page: number
  page_size: number
}

interface AgentStats {
  total_runs: number
  success_rate: number
  runs_24h: number
  unique_agents: number
}

interface CronJob {
  agent_id: string
  schedule: string
  enabled: boolean
  last_run: string | null
  next_run: string | null
}

export interface AgentActivityEvent {
  event: string
  agent_id: string
  message: string
  timestamp?: string
}

export type { AgentInfo, AgentRun, AgentRunsPage, AgentStats, CronJob }

export const useAgentsStore = defineStore('agents', () => {
  const api = useApi()

  const agents = ref<AgentInfo[]>([])
  const runs = ref<AgentRun[]>([])
  const runsTotal = ref(0)
  const runsPage = ref(1)
  const stats = ref<AgentStats | null>(null)
  const cronJobs = ref<CronJob[]>([])
  const activityFeed = ref<AgentActivityEvent[]>([])
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

  async function fetchRuns(agentId: string, page = 1, status?: string) {
    loading.value = true
    error.value = null
    try {
      let url = `/api/agents/${agentId}/runs?page=${page}`
      if (status) url += `&status=${encodeURIComponent(status)}`
      const data = await api.get<AgentRunsPage>(url)
      runs.value = data.runs
      runsTotal.value = data.total
      runsPage.value = data.page
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load runs'
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

  async function triggerAgent(agentId: string): Promise<boolean> {
    try {
      await api.post(`/api/agents/${agentId}/trigger`)
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to trigger agent'
      return false
    }
  }

  function addActivity(event: AgentActivityEvent) {
    activityFeed.value = [
      { ...event, timestamp: event.timestamp ?? new Date().toISOString() },
      ...activityFeed.value,
    ].slice(0, 50)
  }

  return {
    agents,
    runs,
    runsTotal,
    runsPage,
    stats,
    cronJobs,
    activityFeed,
    loading,
    error,
    fetchAgents,
    fetchRuns,
    fetchStats,
    fetchCron,
    triggerAgent,
    addActivity,
  }
})
