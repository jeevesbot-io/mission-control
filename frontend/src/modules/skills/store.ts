import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export interface SkillInfo {
  id?: number
  name: string
  description: string
  source: string
  source_label?: string | null
  file_count?: number
  sha256_hash?: string
  last_indexed_at?: string
  last_changed_at?: string
  has_drift?: boolean
}

export interface ReindexResult {
  indexed: number
  drifted: number
  new: number
  removed: number
  duration_ms: number
}

export const useSkillsStore = defineStore('skills-browser', () => {
  const api = useApi()
  const skills = ref<SkillInfo[]>([])
  const loading = ref(false)
  const reindexing = ref(false)
  const selectedContent = ref('')
  const selectedName = ref('')

  async function fetchSkills(source?: string, q?: string, drifted?: boolean) {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (source) params.set('source', source)
      if (q) params.set('q', q)
      if (drifted) params.set('drifted', 'true')
      const qs = params.toString()
      skills.value = await api.get<SkillInfo[]>(`/api/skills/${qs ? '?' + qs : ''}`)
    } finally {
      loading.value = false
    }
  }

  async function fetchSkillContent(name: string) {
    const data = await api.get<{ name: string; content: string; source_label?: string; sha256_hash?: string; last_changed_at?: string }>(`/api/skills/${encodeURIComponent(name)}`)
    selectedName.value = name
    selectedContent.value = data.content
  }

  async function reindex(source?: string): Promise<ReindexResult> {
    reindexing.value = true
    try {
      const body = source ? { source } : {}
      const result = await api.post<ReindexResult>('/api/skills/reindex', body)
      // Refresh the list after reindex
      await fetchSkills()
      return result
    } finally {
      reindexing.value = false
    }
  }

  return { skills, loading, reindexing, selectedContent, selectedName, fetchSkills, fetchSkillContent, reindex }
})
