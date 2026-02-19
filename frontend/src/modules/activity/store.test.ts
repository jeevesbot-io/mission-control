import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useActivityStore, type ActivityEvent } from './store'

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

function makeEvent(overrides: Partial<ActivityEvent> = {}): ActivityEvent {
  return {
    id: 'evt-1',
    timestamp: '2026-02-19T10:00:00Z',
    actor: 'user',
    action: 'task.created',
    resource_type: 'task',
    resource_id: 'task-1',
    resource_name: 'Test Task',
    details: {},
    module: 'warroom',
    ...overrides,
  }
}

describe('activity store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  // ---------------------------------------------------------------------------
  // fetchFeed
  // ---------------------------------------------------------------------------

  describe('fetchFeed', () => {
    it('loads events and clears loading', async () => {
      const events = [
        makeEvent({ id: 'e1', action: 'task.created' }),
        makeEvent({ id: 'e2', action: 'agent.triggered', module: 'agents' }),
      ]
      mockJsonResponse({ events, total: 2, cursor: '2026-02-19T09:00:00Z' })

      const store = useActivityStore()
      await store.fetchFeed()

      expect(store.events).toHaveLength(2)
      expect(store.events[0]!.action).toBe('task.created')
      expect(store.total).toBe(2)
      expect(store.cursor).toBe('2026-02-19T09:00:00Z')
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useActivityStore()
      await store.fetchFeed()

      expect(store.events).toEqual([])
      expect(store.error).toBeTruthy()
      expect(store.loading).toBe(false)
    })

    it('passes filters to API', async () => {
      mockJsonResponse({ events: [], total: 0, cursor: null })

      const store = useActivityStore()
      await store.fetchFeed(25, { module: 'warroom', actor: 'user' })

      expect(mockFetch).toHaveBeenCalledOnce()
      const url = mockFetch.mock.calls[0]![0] as string
      expect(url).toContain('limit=25')
      expect(url).toContain('module=warroom')
      expect(url).toContain('actor=user')
    })

    it('resets events on new fetch', async () => {
      mockJsonResponse({ events: [makeEvent({ id: 'e1' })], total: 1, cursor: null })

      const store = useActivityStore()
      await store.fetchFeed()
      expect(store.events).toHaveLength(1)

      mockJsonResponse({ events: [makeEvent({ id: 'e2' })], total: 1, cursor: null })
      await store.fetchFeed()
      expect(store.events).toHaveLength(1)
      expect(store.events[0]!.id).toBe('e2')
    })
  })

  // ---------------------------------------------------------------------------
  // loadMore (pagination)
  // ---------------------------------------------------------------------------

  describe('loadMore', () => {
    it('appends events instead of replacing', async () => {
      mockJsonResponse({
        events: [makeEvent({ id: 'e1' })],
        total: 2,
        cursor: '2026-02-19T09:00:00Z',
      })

      const store = useActivityStore()
      await store.fetchFeed()
      expect(store.events).toHaveLength(1)

      mockJsonResponse({
        events: [makeEvent({ id: 'e2' })],
        total: 1,
        cursor: null,
      })

      await store.loadMore()
      expect(store.events).toHaveLength(2)
      expect(store.events[0]!.id).toBe('e1')
      expect(store.events[1]!.id).toBe('e2')
    })

    it('sends cursor as query param', async () => {
      mockJsonResponse({
        events: [makeEvent({ id: 'e1' })],
        total: 1,
        cursor: '2026-02-19T09:00:00Z',
      })

      const store = useActivityStore()
      await store.fetchFeed()

      mockJsonResponse({ events: [], total: 0, cursor: null })
      await store.loadMore()

      const url = mockFetch.mock.calls[1]![0] as string
      expect(url).toContain('cursor=2026-02-19T09%3A00%3A00Z')
    })
  })

  // ---------------------------------------------------------------------------
  // fetchStats
  // ---------------------------------------------------------------------------

  describe('fetchStats', () => {
    it('loads stats', async () => {
      mockJsonResponse({
        total_events: 42,
        by_module: { warroom: 20, agents: 15 },
        by_action: { 'task.created': 10 },
        last_24h: 12,
      })

      const store = useActivityStore()
      await store.fetchStats()

      expect(store.stats).not.toBeNull()
      expect(store.stats!.total_events).toBe(42)
      expect(store.stats!.last_24h).toBe(12)
    })

    it('sets stats to null on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useActivityStore()
      await store.fetchStats()

      expect(store.stats).toBeNull()
    })
  })

  // ---------------------------------------------------------------------------
  // prependEvent (live WebSocket updates)
  // ---------------------------------------------------------------------------

  describe('prependEvent', () => {
    it('adds event to the beginning of the list', async () => {
      mockJsonResponse({ events: [makeEvent({ id: 'e1' })], total: 1, cursor: null })

      const store = useActivityStore()
      await store.fetchFeed()

      store.prependEvent(makeEvent({ id: 'e-new', action: 'agent.triggered' }))

      expect(store.events).toHaveLength(2)
      expect(store.events[0]!.id).toBe('e-new')
      expect(store.total).toBe(2)
    })
  })
})
