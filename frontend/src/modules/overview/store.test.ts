import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useOverviewStore } from './store'
import type { OverviewData } from './store'

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

const mockOverviewData: OverviewData = {
  stats: {
    agents_active: 1,
    events_this_week: 5,
    emails_processed: 17,
    tasks_pending: 3,
  },
  agent_summary: {
    total_entries: 61,
    info_count: 57,
    warning_count: 3,
    entries_24h: 12,
    unique_agents: 1,
    health_rate: 93.4,
  },
  upcoming_events: [
    {
      id: 1,
      child: 'Natty',
      summary: 'World Book Day',
      event_date: '2026-03-03',
      event_end_date: null,
      event_time: null,
      days_away: 3,
    },
    {
      id: 2,
      child: 'Elodie',
      summary: 'Sports Day',
      event_date: '2026-03-05',
      event_end_date: null,
      event_time: '14:00:00',
      days_away: 5,
    },
  ],
  recent_activity: [
    {
      id: '1',
      agent_id: 'matron',
      level: 'info',
      message: 'Urgent check: No unread emails',
      created_at: '2026-02-13T08:00:00Z',
    },
  ],
  health: {
    status: 'healthy',
    database: true,
    uptime_seconds: 3600.0,
    version: '0.1.0',
  },
}

describe('overview store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('fetchOverview', () => {
    it('loads full overview data', async () => {
      mockJsonResponse(mockOverviewData)

      const store = useOverviewStore()
      await store.fetchOverview()

      expect(store.data).toEqual(mockOverviewData)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'Server error' }, 500)

      const store = useOverviewStore()
      await store.fetchOverview()

      expect(store.data).toBeNull()
      expect(store.error).toBeTruthy()
    })

    it('has correct stats', async () => {
      mockJsonResponse(mockOverviewData)

      const store = useOverviewStore()
      await store.fetchOverview()

      expect(store.data?.stats.agents_active).toBe(1)
      expect(store.data?.stats.events_this_week).toBe(5)
      expect(store.data?.stats.emails_processed).toBe(17)
      expect(store.data?.stats.tasks_pending).toBe(3)
    })

    it('has correct upcoming events', async () => {
      mockJsonResponse(mockOverviewData)

      const store = useOverviewStore()
      await store.fetchOverview()

      expect(store.data?.upcoming_events).toHaveLength(2)
      expect(store.data?.upcoming_events[0]?.child).toBe('Natty')
      expect(store.data?.upcoming_events[1]?.child).toBe('Elodie')
    })

    it('has correct health data', async () => {
      mockJsonResponse(mockOverviewData)

      const store = useOverviewStore()
      await store.fetchOverview()

      expect(store.data?.health.status).toBe('healthy')
      expect(store.data?.health.database).toBe(true)
    })

    it('handles empty data gracefully', async () => {
      const emptyData: OverviewData = {
        ...mockOverviewData,
        upcoming_events: [],
        recent_activity: [],
        stats: { agents_active: 0, events_this_week: 0, emails_processed: 0, tasks_pending: 0 },
      }
      mockJsonResponse(emptyData)

      const store = useOverviewStore()
      await store.fetchOverview()

      expect(store.data?.upcoming_events).toEqual([])
      expect(store.data?.recent_activity).toEqual([])
      expect(store.data?.stats.agents_active).toBe(0)
    })
  })
})
