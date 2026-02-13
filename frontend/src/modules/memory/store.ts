import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

interface MemorySection {
  heading: string
  slug: string
  content: string
  level: number
}

interface MemoryFileInfo {
  date: string
  filename: string
  size: number
  section_count: number
  preview: string
}

interface DailyMemory {
  date: string
  filename: string
  content: string
  sections: MemorySection[]
}

interface LongTermMemory {
  content: string
  sections: MemorySection[]
}

interface SearchHit {
  filename: string
  date: string | null
  line_number: number
  section_heading: string | null
  snippet: string
}

interface MemoryStats {
  total_files: number
  latest_date: string | null
  total_size_bytes: number
  has_long_term: boolean
}

export const useMemoryStore = defineStore('memory', () => {
  const api = useApi()

  const files = ref<MemoryFileInfo[]>([])
  const currentDaily = ref<DailyMemory | null>(null)
  const longTerm = ref<LongTermMemory | null>(null)
  const searchResults = ref<SearchHit[]>([])
  const searchQuery = ref('')
  const stats = ref<MemoryStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFiles() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ files: MemoryFileInfo[]; total: number }>('/api/memory/files')
      files.value = data.files
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load files'
    } finally {
      loading.value = false
    }
  }

  async function fetchDaily(date: string) {
    loading.value = true
    error.value = null
    try {
      currentDaily.value = await api.get<DailyMemory>(`/api/memory/files/${date}`)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load daily memory'
      currentDaily.value = null
    } finally {
      loading.value = false
    }
  }

  async function fetchLongTerm() {
    loading.value = true
    error.value = null
    try {
      longTerm.value = await api.get<LongTermMemory>('/api/memory/long-term')
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load long-term memory'
      longTerm.value = null
    } finally {
      loading.value = false
    }
  }

  async function search(query: string) {
    if (query.length < 2) {
      searchResults.value = []
      searchQuery.value = ''
      return
    }
    loading.value = true
    error.value = null
    searchQuery.value = query
    try {
      const data = await api.get<{ hits: SearchHit[]; total: number }>(
        `/api/memory/search?q=${encodeURIComponent(query)}`,
      )
      searchResults.value = data.hits
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Search failed'
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      stats.value = await api.get<MemoryStats>('/api/memory/stats')
    } catch {
      stats.value = null
    }
  }

  return {
    files,
    currentDaily,
    longTerm,
    searchResults,
    searchQuery,
    stats,
    loading,
    error,
    fetchFiles,
    fetchDaily,
    fetchLongTerm,
    search,
    fetchStats,
  }
})
