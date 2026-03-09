import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export interface SkillInfo {
  name: string
  description: string
  source: 'managed' | 'workspace' | 'agent'
}

export const useSkillsStore = defineStore('skills-browser', () => {
  const api = useApi()
  const skills = ref<SkillInfo[]>([])
  const loading = ref(false)
  const selectedContent = ref('')
  const selectedName = ref('')

  async function fetchSkills() {
    loading.value = true
    try {
      skills.value = await api.get<SkillInfo[]>('/api/skills/')
    } finally {
      loading.value = false
    }
  }

  async function fetchSkillContent(name: string) {
    const data = await api.get<{ name: string; content: string }>(`/api/skills/${encodeURIComponent(name)}`)
    selectedName.value = name
    selectedContent.value = data.content
  }

  return { skills, loading, selectedContent, selectedName, fetchSkills, fetchSkillContent }
})
