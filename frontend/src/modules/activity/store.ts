import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export interface ActivityEvent {
  id: string
  timestamp: string
  actor: string
  action: string
  resource_type: string
  resource_id: string | null
  resource_name: string | null
  details: Record<string, unknown>
  module: string
}

interface ActivityFeedResponse {
  events: ActivityEvent[]
  total: number
  cursor: string | null
}

export interface ActivityStats {
  total_events: number
  by_module: Record<string, number>
  by_action: Record<string, number>
  last_24h: number
}

export const useActivityStore = defineStore('activity', () => {
  const api = useApi()

  const events = ref<ActivityEvent[]>([])
  const total = ref(0)
  const cursor = ref<string | null>(null)
  const stats = ref<ActivityStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFeed(
    limit = 50,
    filters?: { module?: string; actor?: string; action?: string },
    reset = true,
  ) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ limit: String(limit) })
      if (!reset && cursor.value) params.set('cursor', cursor.value)
      if (filters?.module) params.set('module', filters.module)
      if (filters?.actor) params.set('actor', filters.actor)
      if (filters?.action) params.set('action', filters.action)

      const data = await api.get<ActivityFeedResponse>(`/api/activity/feed?${params}`)

      if (reset) {
        events.value = data.events
      } else {
        events.value = [...events.value, ...data.events]
      }
      total.value = data.total
      cursor.value = data.cursor
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load activity feed'
    } finally {
      loading.value = false
    }
  }

  async function loadMore(
    limit = 50,
    filters?: { module?: string; actor?: string; action?: string },
  ) {
    return fetchFeed(limit, filters, false)
  }

  async function fetchStats() {
    try {
      stats.value = await api.get<ActivityStats>('/api/activity/stats')
    } catch {
      stats.value = null
    }
  }

  function prependEvent(event: ActivityEvent) {
    events.value = [event, ...events.value]
    total.value++
  }

  return {
    events,
    total,
    cursor,
    stats,
    loading,
    error,
    fetchFeed,
    loadMore,
    fetchStats,
    prependEvent,
  }
})
