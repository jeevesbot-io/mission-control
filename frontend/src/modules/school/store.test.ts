import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSchoolStore } from './store'

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

describe('school store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('fetchCalendar', () => {
    it('loads calendar events', async () => {
      const calData = {
        events: [
          {
            id: 'abc123',
            summary: 'Swimming',
            start_date: null,
            start_datetime: '2026-02-15T08:30:00Z',
            end_date: null,
            end_datetime: '2026-02-15T09:00:00Z',
            all_day: false,
            child: null,
          },
          {
            id: 'def456',
            summary: 'Elodie Rugby',
            start_date: null,
            start_datetime: '2026-02-16T15:30:00Z',
            end_date: null,
            end_datetime: '2026-02-16T16:30:00Z',
            all_day: false,
            child: 'Elodie',
          },
        ],
        total: 2,
        window_start: '2026-02-14',
        window_end: '2026-02-21',
      }
      mockJsonResponse(calData)

      const store = useSchoolStore()
      await store.fetchCalendar()

      expect(store.calendarEvents).toHaveLength(2)
      expect(store.calendarEvents[0]!.summary).toBe('Swimming')
      expect(store.calendarEvents[1]!.child).toBe('Elodie')
      expect(store.calendarWindowStart).toBe('2026-02-14')
      expect(store.calendarWindowEnd).toBe('2026-02-21')
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useSchoolStore()
      await store.fetchCalendar()

      expect(store.calendarEvents).toEqual([])
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchEmails', () => {
    it('loads emails', async () => {
      const data = {
        emails: [
          {
            id: 1,
            email_id: 'e1',
            subject: 'Test',
            sender: 'school@test.com',
            child: 'Natty',
            school_id: 'qe',
            preview: 'Hello',
            processed_at: '2026-02-13T10:00:00Z',
          },
        ],
        total: 1,
      }
      mockJsonResponse(data)

      const store = useSchoolStore()
      await store.fetchEmails()

      expect(store.emails).toHaveLength(1)
      expect(store.emails[0]!.subject).toBe('Test')
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useSchoolStore()
      await store.fetchEmails()

      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchTasks', () => {
    it('loads tasks', async () => {
      const data = {
        tasks: [
          {
            id: '1',
            content: 'Book costume',
            description: null,
            due_date: '2026-03-01',
            todoist_id: 't1',
            created_at: '2026-02-13T10:00:00Z',
          },
        ],
        total: 1,
      }
      mockJsonResponse(data)

      const store = useSchoolStore()
      await store.fetchTasks()

      expect(store.tasks).toHaveLength(1)
      expect(store.tasks[0]!.content).toBe('Book costume')
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useSchoolStore()
      await store.fetchTasks()

      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchStats', () => {
    it('loads stats', async () => {
      const stats = {
        upcoming_events: 10,
        total_emails: 17,
        total_tasks: 3,
      }
      mockJsonResponse(stats)

      const store = useSchoolStore()
      await store.fetchStats()

      expect(store.stats).toEqual(stats)
    })

    it('handles failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useSchoolStore()
      await store.fetchStats()

      expect(store.stats).toBeNull()
    })
  })
})
