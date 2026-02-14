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

  describe('fetchEvents', () => {
    it('loads events', async () => {
      const events = [
        {
          id: 1,
          child: 'Natty',
          summary: 'PSA Donut Sale',
          description: 'After school',
          event_date: '2026-02-13',
          event_end_date: null,
          event_time: null,
          school_id: 'qe',
        },
      ]
      mockJsonResponse({ events, total: 1 })

      const store = useSchoolStore()
      await store.fetchEvents()

      expect(store.events).toEqual(events)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'Server error' }, 500)

      const store = useSchoolStore()
      await store.fetchEvents()

      expect(store.events).toEqual([])
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchEmails', () => {
    it('loads emails', async () => {
      const emails = [
        {
          id: 1,
          email_id: '10',
          subject: 'Field Trip',
          sender: 'teacher@school.edu',
          child: 'Elodie',
          school_id: 'county',
          preview: 'Permission slip...',
          processed_at: '2026-02-10T09:30:00Z',
        },
      ]
      mockJsonResponse({ emails, total: 1 })

      const store = useSchoolStore()
      await store.fetchEmails()

      expect(store.emails).toEqual(emails)
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'Error' }, 500)

      const store = useSchoolStore()
      await store.fetchEmails()

      expect(store.emails).toEqual([])
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchTasks', () => {
    it('loads tasks', async () => {
      const tasks = [
        {
          id: 'task-1',
          content: 'Submit homework',
          description: 'Math worksheet',
          due_date: '2026-02-15',
          todoist_id: 'abc123',
          created_at: '2026-02-10T09:00:00Z',
        },
      ]
      mockJsonResponse({ tasks, total: 1 })

      const store = useSchoolStore()
      await store.fetchTasks()

      expect(store.tasks).toEqual(tasks)
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'Error' }, 500)

      const store = useSchoolStore()
      await store.fetchTasks()

      expect(store.tasks).toEqual([])
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchStats', () => {
    it('loads stats', async () => {
      const stats = {
        upcoming_events: 3,
        total_emails: 17,
        total_tasks: 3,
      }
      mockJsonResponse(stats)

      const store = useSchoolStore()
      await store.fetchStats()

      expect(store.stats).toEqual(stats)
    })

    it('sets null on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useSchoolStore()
      await store.fetchStats()

      expect(store.stats).toBeNull()
    })
  })
})
