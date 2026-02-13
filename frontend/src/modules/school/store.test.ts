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
          title: 'Conference',
          description: 'Meet teachers',
          start_time: '2026-02-20T14:00:00Z',
          end_time: '2026-02-20T16:00:00Z',
          location: 'Room 201',
          all_day: false,
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
          subject: 'Field Trip',
          sender: 'teacher@school.edu',
          preview: 'Permission slip...',
          received_at: '2026-02-10T09:30:00Z',
          is_read: false,
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
          priority: 3,
          due_date: '2026-02-15',
          is_completed: false,
          project_name: 'School',
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
        unread_emails: 5,
        pending_tasks: 8,
        completed_today: 2,
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
