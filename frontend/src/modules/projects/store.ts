import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export interface ProjectDoc {
  title: string
  url: string
}

export interface Project {
  id: string
  name: string
  icon: string
  color: string
  description: string | null
  docs: ProjectDoc[]
  status: string
  order: number
  created_at: string
  updated_at: string
  task_count: number
  agent_count: number
}

export interface TaskSummary {
  id: number
  title: string
  state: string
  priority: number
  agent_id: string
  tags: string[]
  created_at: string | null
  updated_at: string | null
  completed_at: string | null
}

export interface ProjectDetail extends Project {
  tasks: TaskSummary[]
  agent_ids: string[]
}

export const useProjectsStore = defineStore('projects', () => {
  const api = useApi()

  const projects = ref<Project[]>([])
  const selectedProject = ref<ProjectDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProjects() {
    loading.value = true
    error.value = null
    try {
      projects.value = await api.get<Project[]>('/api/projects/')
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load projects'
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id: string) {
    loading.value = true
    error.value = null
    try {
      selectedProject.value = await api.get<ProjectDetail>(`/api/projects/${id}`)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load project'
    } finally {
      loading.value = false
    }
  }

  async function createProject(data: {
    id: string
    name: string
    icon?: string
    color?: string
    description?: string
    status?: string
  }) {
    const result = await api.post<Project>('/api/projects/', data)
    projects.value.push(result)
    return result
  }

  async function updateProject(id: string, data: Record<string, unknown>) {
    const result = await api.patch<Project>(`/api/projects/${id}`, data)
    const idx = projects.value.findIndex((p) => p.id === id)
    if (idx !== -1) projects.value[idx] = result
    if (selectedProject.value?.id === id) {
      selectedProject.value = { ...selectedProject.value, ...result }
    }
    return result
  }

  async function deleteProject(id: string) {
    await api.delete(`/api/projects/${id}`)
    projects.value = projects.value.filter((p) => p.id !== id)
    if (selectedProject.value?.id === id) selectedProject.value = null
  }

  return {
    projects,
    selectedProject,
    loading,
    error,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
  }
})
