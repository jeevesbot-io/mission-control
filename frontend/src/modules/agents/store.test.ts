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
    it('loads agent list', async () => {
      const agents = [
        { agent_id: 'test-agent', last_run: '2026-01-15T10:00:00Z', last_status: 'success', total_runs: 5 },
      ]
      mockJsonResponse(agents)

      const store = useAgentsStore()
      await store.fetchAgents()

      expect(store.agents).toEqual(agents)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'Server error' }, 500)

      const store = useAgentsStore()
      await store.fetchAgents()

      expect(store.agents).toEqual([])
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchRuns', () => {
    it('loads paginated runs', async () => {
      const runs = [
        {
          id: 'run-1',
          agent_id: 'test-agent',
          run_type: 'scheduled',
          trigger: 'cron',
          status: 'success',
          summary: 'Done',
          duration_ms: 1500,
          tokens_used: 100,
          created_at: '2026-01-15T10:00:00Z',
        },
      ]
      mockJsonResponse({ runs, total: 1, page: 1, page_size: 20 })

      const store = useAgentsStore()
      await store.fetchRuns('test-agent')

      expect(store.runs).toEqual(runs)
      expect(store.runsTotal).toBe(1)
      expect(store.runsPage).toBe(1)
    })

    it('passes status filter', async () => {
      mockJsonResponse({ runs: [], total: 0, page: 1, page_size: 20 })

      const store = useAgentsStore()
      await store.fetchRuns('test-agent', 1, 'error')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('status=error'),
        expect.anything(),
      )
    })
  })

  describe('fetchStats', () => {
    it('loads stats', async () => {
      const stats = { total_runs: 100, success_rate: 95.0, runs_24h: 12, unique_agents: 3 }
      mockJsonResponse(stats)

      const store = useAgentsStore()
      await store.fetchStats()

      expect(store.stats).toEqual(stats)
    })

    it('sets null on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useAgentsStore()
      await store.fetchStats()

      expect(store.stats).toBeNull()
    })
  })

  describe('fetchCron', () => {
    it('loads cron jobs', async () => {
      const jobs = [
        { agent_id: 'daily', schedule: '0 8 * * *', enabled: true, last_run: null, next_run: null },
      ]
      mockJsonResponse({ jobs })

      const store = useAgentsStore()
      await store.fetchCron()

      expect(store.cronJobs).toEqual(jobs)
    })

    it('sets empty on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useAgentsStore()
      await store.fetchCron()

      expect(store.cronJobs).toEqual([])
    })
  })

  describe('triggerAgent', () => {
    it('returns true on success', async () => {
      mockJsonResponse({ success: true, message: 'Triggered', agent_id: 'test' })

      const store = useAgentsStore()
      const result = await store.triggerAgent('test')

      expect(result).toBe(true)
    })

    it('returns false on failure', async () => {
      mockJsonResponse({ detail: 'Gateway error' }, 502)

      const store = useAgentsStore()
      const result = await store.triggerAgent('test')

      expect(result).toBe(false)
      expect(store.error).toBeTruthy()
    })
  })

  describe('addActivity', () => {
    it('prepends activity events', () => {
      const store = useAgentsStore()
      store.addActivity({ event: 'trigger', agent_id: 'test', message: 'Triggered' })
      store.addActivity({ event: 'complete', agent_id: 'test', message: 'Done' })

      expect(store.activityFeed).toHaveLength(2)
      expect(store.activityFeed[0]!.message).toBe('Done')
      expect(store.activityFeed[1]!.message).toBe('Triggered')
    })

    it('caps at 50 events', () => {
      const store = useAgentsStore()
      for (let i = 0; i < 60; i++) {
        store.addActivity({ event: 'trigger', agent_id: 'test', message: `Event ${i}` })
      }

      expect(store.activityFeed).toHaveLength(50)
    })
  })
})
