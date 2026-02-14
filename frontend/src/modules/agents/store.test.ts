import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAgentsStore } from './store'

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
  mockFetch.mockReset()
})

function mockJsonResponse(data: unknown, status = 200) {
  return mockFetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  })
}

describe('agents store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('fetchAgents', () => {
    it('loads agents list', async () => {
      const agents = [
        {
          agent_id: 'matron',
          last_activity: '2026-02-14T09:31:00Z',
          last_message: 'Urgent check: No unread emails',
          last_level: 'info',
          total_entries: 61,
          warning_count: 3,
        },
      ]
      mockJsonResponse(agents)

      const store = useAgentsStore()
      await store.fetchAgents()

      expect(store.agents).toEqual(agents)
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'Error' }, 500)

      const store = useAgentsStore()
      await store.fetchAgents()

      expect(store.agents).toEqual([])
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchStats', () => {
    it('loads stats', async () => {
      const stats = {
        total_entries: 61,
        unique_agents: 1,
        entries_24h: 12,
        warning_count: 3,
        health_rate: 93.4,
      }
      mockJsonResponse(stats)

      const store = useAgentsStore()
      await store.fetchStats()

      expect(store.stats).toEqual(stats)
    })

    it('handles failure gracefully', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useAgentsStore()
      await store.fetchStats()

      expect(store.stats).toBeNull()
    })
  })

  describe('fetchCron', () => {
    it('loads cron jobs', async () => {
      const jobs = [
        { agent_id: 'matron', schedule: '*/30 7-21 * * *', enabled: true },
      ]
      mockJsonResponse({ jobs })

      const store = useAgentsStore()
      await store.fetchCron()

      expect(store.cronJobs).toEqual(jobs)
    })

    it('handles failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useAgentsStore()
      await store.fetchCron()

      expect(store.cronJobs).toEqual([])
    })
  })

  describe('fetchLog', () => {
    it('loads log entries', async () => {
      const entries = [
        {
          id: 1,
          agent_id: 'matron',
          level: 'info',
          message: 'Urgent check completed',
          metadata: { new_emails: 0 },
          created_at: '2026-02-14T09:31:00Z',
        },
      ]
      mockJsonResponse({ entries, total: 1 })

      const store = useAgentsStore()
      await store.fetchLog('matron')

      expect(store.logEntries).toEqual(entries)
      expect(store.logTotal).toBe(1)
    })

    it('handles failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useAgentsStore()
      await store.fetchLog('matron')

      expect(store.error).toBeTruthy()
    })
  })

  describe('triggerAgent', () => {
    it('returns true on success', async () => {
      mockJsonResponse({ success: true, message: 'ok', agent_id: 'matron' })

      const store = useAgentsStore()
      const result = await store.triggerAgent('matron')

      expect(result).toBe(true)
    })

    it('returns false on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 502)

      const store = useAgentsStore()
      const result = await store.triggerAgent('matron')

      expect(result).toBe(false)
    })
  })

  describe('addActivity', () => {
    it('prepends activity to feed', () => {
      const store = useAgentsStore()
      store.addActivity({
        event: 'trigger',
        agent_id: 'matron',
        message: 'Triggered manually',
      })

      expect(store.activityFeed).toHaveLength(1)
      expect(store.activityFeed[0]!.agent_id).toBe('matron')
      expect(store.activityFeed[0]!.timestamp).toBeTruthy()
    })
  })
})
