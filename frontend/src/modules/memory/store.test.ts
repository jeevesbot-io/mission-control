import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMemoryStore } from './store'

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

describe('memory store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('fetchFiles', () => {
    it('loads file list', async () => {
      const files = [
        { date: '2026-01-15', filename: '2026-01-15.md', size: 500, section_count: 3, preview: 'Hello' },
      ]
      mockJsonResponse({ files, total: 1 })

      const store = useMemoryStore()
      await store.fetchFiles()

      expect(store.files).toEqual(files)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'Server error' }, 500)

      const store = useMemoryStore()
      await store.fetchFiles()

      expect(store.files).toEqual([])
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchDaily', () => {
    it('loads daily memory', async () => {
      const daily = {
        date: '2026-01-15',
        filename: '2026-01-15.md',
        content: '# 2026-01-15\n\nContent here',
        sections: [{ heading: '2026-01-15', slug: '2026-01-15', content: 'Content here', level: 1 }],
      }
      mockJsonResponse(daily)

      const store = useMemoryStore()
      await store.fetchDaily('2026-01-15')

      expect(store.currentDaily).toEqual(daily)
      expect(store.loading).toBe(false)
    })

    it('sets error on 404', async () => {
      mockJsonResponse({ detail: 'Not found' }, 404)

      const store = useMemoryStore()
      await store.fetchDaily('1999-01-01')

      expect(store.currentDaily).toBeNull()
      expect(store.error).toBeTruthy()
    })
  })

  describe('fetchLongTerm', () => {
    it('loads long-term memory', async () => {
      const lt = {
        content: '# MEMORY.md\n\nLong-term content',
        sections: [{ heading: 'MEMORY.md', slug: 'memorymd', content: 'Long-term content', level: 1 }],
      }
      mockJsonResponse(lt)

      const store = useMemoryStore()
      await store.fetchLongTerm()

      expect(store.longTerm).toEqual(lt)
    })
  })

  describe('search', () => {
    it('returns search hits', async () => {
      const hits = [
        { filename: '2026-01-15.md', date: '2026-01-15', line_number: 5, section_heading: 'Tasks', snippet: 'auth module fix' },
      ]
      mockJsonResponse({ query: 'auth', hits, total: 1 })

      const store = useMemoryStore()
      await store.search('auth')

      expect(store.searchResults).toEqual(hits)
      expect(store.searchQuery).toBe('auth')
    })

    it('skips search for short queries', async () => {
      const store = useMemoryStore()
      await store.search('a')

      expect(mockFetch).not.toHaveBeenCalled()
      expect(store.searchResults).toEqual([])
    })
  })

  describe('fetchStats', () => {
    it('loads stats', async () => {
      const stats = { total_files: 5, latest_date: '2026-01-15', total_size_bytes: 12000, has_long_term: true }
      mockJsonResponse(stats)

      const store = useMemoryStore()
      await store.fetchStats()

      expect(store.stats).toEqual(stats)
    })

    it('sets null on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useMemoryStore()
      await store.fetchStats()

      expect(store.stats).toBeNull()
    })
  })
})
