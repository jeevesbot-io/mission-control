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

export interface DriftEntry {
  skill_name: string
  source_label: string
  old_hash: string
  new_hash: string
  old_file_count: number | null
  new_file_count: number | null
  files_changed: Array<{ path: string; action: string }> | null
  detected_at: string
}

export interface SkillStats {
  total_skills: number
  by_source: Record<string, number>
  drifted_last_7d: number
  last_full_index: string | null
}

export const useSkillsStore = defineStore('skills-browser', () => {
  const api = useApi()
  const skills = ref<SkillInfo[]>([])
  const loading = ref(false)
  const reindexing = ref(false)
  const selectedContent = ref('')
  const selectedName = ref('')
  const stats = ref<SkillStats | null>(null)
  const driftEntries = ref<DriftEntry[]>([])

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

  async function fetchStats() {
    stats.value = await api.get<SkillStats>('/api/skills/stats')
  }

  async function fetchDrift(since?: string) {
    const params = new URLSearchParams()
    if (since) params.set('since', since)
    const qs = params.toString()
    driftEntries.value = await api.get<DriftEntry[]>(`/api/skills/drift${qs ? '?' + qs : ''}`)
  }

  return { skills, loading, reindexing, selectedContent, selectedName, stats, driftEntries, fetchSkills, fetchSkillContent, reindex, fetchStats, fetchDrift }
})
