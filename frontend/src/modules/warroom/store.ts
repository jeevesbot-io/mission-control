import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useApi } from '@/composables/useApi'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Reference {
  id: string
  title: string
  url: string
  type: 'link' | 'obsidian' | 'doc'
  createdAt: string
}

export interface Task {
  id: string
  title: string
  description: string
  status: 'backlog' | 'todo' | 'in-progress' | 'done'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  project: string | null
  tags: string[]
  skill: string | null
  schedule: string | null
  scheduledAt: string | null
  references: Reference[]
  blockedBy: string[]
  blocks: string[]
  startedAt: string | null
  completedAt: string | null
  result: string | null
  error: string | null
  pickedUp: boolean
  createdAt: string
  updatedAt: string
  estimatedHours: number | null
  actualHours: number | null
}

export interface Project {
  id: string
  name: string
  icon: string
  color: string
  description: string | null
  status: 'active' | 'paused' | 'archived'
  order: number
  task_count?: number
}

export interface Skill {
  id: string
  name: string
  description: string
  source: 'bundled' | 'managed' | 'workspace'
  enabled: boolean
  path: string
  hasMetadata: boolean
}

export interface UsageTier {
  label: string
  percent: number
  resetsIn: string
}

export interface UsageData {
  model: string
  tiers: UsageTier[]
}

export interface HeartbeatData {
  lastHeartbeat: number | null
}

export interface WarRoomStats {
  in_progress_count: number
  todo_count: number
  last_heartbeat: number | null
  active_model: string
}

export interface CalendarDay {
  memory: boolean
  tasks: string[]
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useWarRoomStore = defineStore('warroom', () => {
  const api = useApi()

  // State
  const tasks = ref<Task[]>([])
  const projects = ref<Project[]>([])
  const availableTags = ref<string[]>([])
  const skills = ref<Skill[]>([])
  const usage = ref<UsageData | null>(null)
  const models = ref<string[]>([])
  const heartbeat = ref<HeartbeatData | null>(null)
  const calendarData = ref<Record<string, CalendarDay>>({})

  // Filter state
  const filterProject = ref<string | null>(null)
  const filterPriority = ref<string | null>(null)
  const filterTags = ref<string[]>([])

  // UI state
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------

  const filteredTasks = computed(() => {
    let result = tasks.value
    if (filterProject.value === 'untagged') {
      result = result.filter((t) => !t.project)
    } else if (filterProject.value) {
      result = result.filter((t) => t.project === filterProject.value)
    }
    if (filterPriority.value) {
      result = result.filter((t) => t.priority === filterPriority.value)
    }
    if (filterTags.value.length > 0) {
      result = result.filter((t) => filterTags.value.some((tag) => t.tags.includes(tag)))
    }
    return result
  })

  const tasksByStatus = computed(() => ({
    backlog: filteredTasks.value.filter((t) => t.status === 'backlog'),
    todo: filteredTasks.value.filter((t) => t.status === 'todo'),
    'in-progress': filteredTasks.value.filter((t) => t.status === 'in-progress'),
    done: filteredTasks.value.filter((t) => t.status === 'done'),
  }))

  const projectsWithCounts = computed(() =>
    projects.value.map((p) => ({
      ...p,
      task_count: tasks.value.filter((t) => t.project === p.id).length,
    })),
  )

  const activeProjectsWithCounts = computed(() =>
    projectsWithCounts.value.filter((p) => p.status === 'active'),
  )

  // ---------------------------------------------------------------------------
  // Tasks
  // ---------------------------------------------------------------------------

  async function fetchTasks() {
    loading.value = true
    error.value = null
    try {
      tasks.value = await api.get<Task[]>('/api/warroom/tasks')
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load tasks'
    } finally {
      loading.value = false
    }
  }

  async function createTask(payload: Partial<Task>): Promise<Task | null> {
    try {
      const task = await api.post<Task>('/api/warroom/tasks', payload)
      tasks.value.push(task)
      return task
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to create task'
      return null
    }
  }

  async function updateTask(id: string, payload: Partial<Task>): Promise<Task | null> {
    try {
      const task = await api.put<Task>(`/api/warroom/tasks/${id}`, payload)
      const idx = tasks.value.findIndex((t) => t.id === id)
      if (idx !== -1) tasks.value[idx] = task
      return task
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to update task'
      return null
    }
  }

  async function deleteTask(id: string): Promise<boolean> {
    try {
      await api.delete(`/api/warroom/tasks/${id}`)
      tasks.value = tasks.value.filter((t) => t.id !== id)
      return true
    } catch {
      return false
    }
  }

  async function moveTask(id: string, newStatus: Task['status']): Promise<void> {
    // Optimistic update — instant UI response
    const task = tasks.value.find((t) => t.id === id)
    if (task) task.status = newStatus
    await updateTask(id, { status: newStatus })
  }

  async function runTask(id: string): Promise<boolean> {
    try {
      await api.post(`/api/warroom/tasks/${id}/run`)
      return true
    } catch {
      return false
    }
  }

  async function addReference(taskId: string, payload: Omit<Reference, 'id' | 'createdAt'>): Promise<Reference | null> {
    try {
      const ref = await api.post<Reference>(`/api/warroom/tasks/${taskId}/references`, payload)
      const task = tasks.value.find((t) => t.id === taskId)
      if (task) task.references.push(ref)
      return ref
    } catch {
      return null
    }
  }

  async function deleteReference(taskId: string, refId: string): Promise<void> {
    try {
      await api.delete(`/api/warroom/tasks/${taskId}/references/${refId}`)
      const task = tasks.value.find((t) => t.id === taskId)
      if (task) task.references = task.references.filter((r) => r.id !== refId)
    } catch { /* noop */ }
  }

  function isTaskBlocked(task: Task): boolean {
    const blockedBy = task.blockedBy || []
    if (blockedBy.length === 0) return false
    return blockedBy.some((id) => {
      const blocker = tasks.value.find((t) => t.id === id)
      return !blocker || blocker.status !== 'done'
    })
  }

  // ---------------------------------------------------------------------------
  // Projects
  // ---------------------------------------------------------------------------

  async function fetchProjects() {
    try {
      projects.value = await api.get<Project[]>('/api/warroom/projects')
    } catch {
      projects.value = []
    }
  }

  async function createProject(payload: Omit<Project, 'task_count'>): Promise<Project | null> {
    try {
      const proj = await api.post<Project>('/api/warroom/projects', payload)
      projects.value.push(proj)
      return proj
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to create project'
      return null
    }
  }

  async function updateProject(id: string, payload: Partial<Project>): Promise<Project | null> {
    try {
      const proj = await api.put<Project>(`/api/warroom/projects/${id}`, payload)
      const idx = projects.value.findIndex((p) => p.id === id)
      if (idx !== -1) projects.value[idx] = proj
      return proj
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to update project'
      return null
    }
  }

  async function deleteProject(id: string): Promise<boolean> {
    try {
      await api.delete(`/api/warroom/projects/${id}`)
      projects.value = projects.value.filter((p) => p.id !== id)
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to delete project'
      return false
    }
  }

  // ---------------------------------------------------------------------------
  // Tags
  // ---------------------------------------------------------------------------

  async function fetchTags() {
    try {
      availableTags.value = await api.get<string[]>('/api/warroom/tags')
    } catch {
      availableTags.value = []
    }
  }

  // ---------------------------------------------------------------------------
  // Filters
  // ---------------------------------------------------------------------------

  function setProjectFilter(id: string | null) {
    filterProject.value = id
  }

  function setPriorityFilter(priority: string | null) {
    filterPriority.value = priority
  }

  function setTagFilter(tags: string[]) {
    filterTags.value = tags
  }

  function clearFilters() {
    filterProject.value = null
    filterPriority.value = null
    filterTags.value = []
  }

  // ---------------------------------------------------------------------------
  // Usage / Models
  // ---------------------------------------------------------------------------

  async function fetchUsage() {
    try {
      usage.value = await api.get<UsageData>('/api/warroom/usage')
    } catch {
      usage.value = null
    }
  }

  async function fetchModels() {
    try {
      models.value = await api.get<string[]>('/api/warroom/models')
    } catch {
      models.value = []
    }
  }

  async function setModel(model: string): Promise<boolean> {
    try {
      await api.post('/api/warroom/model', { model })
      if (usage.value) usage.value.model = model
      return true
    } catch {
      return false
    }
  }

  // ---------------------------------------------------------------------------
  // Heartbeat
  // ---------------------------------------------------------------------------

  async function fetchHeartbeat() {
    try {
      heartbeat.value = await api.get<HeartbeatData>('/api/warroom/heartbeat')
    } catch {
      heartbeat.value = null
    }
  }

  // ---------------------------------------------------------------------------
  // Skills
  // ---------------------------------------------------------------------------

  async function fetchSkills() {
    loading.value = true
    try {
      skills.value = await api.get<Skill[]>('/api/warroom/skills')
    } catch {
      skills.value = []
    } finally {
      loading.value = false
    }
  }

  async function toggleSkill(id: string, enabled: boolean) {
    try {
      const updated = await api.post<Skill>(`/api/warroom/skills/${id}/toggle`, { enabled })
      const idx = skills.value.findIndex((s) => s.id === id)
      if (idx !== -1) skills.value[idx] = updated
    } catch { /* noop */ }
  }

  async function createSkill(payload: { name: string; description?: string; instructions?: string }): Promise<Skill | null> {
    try {
      const skill = await api.post<Skill>('/api/warroom/skills', payload)
      skills.value.push(skill)
      return skill
    } catch {
      return null
    }
  }

  async function deleteSkill(id: string): Promise<boolean> {
    try {
      await api.delete(`/api/warroom/skills/${id}`)
      skills.value = skills.value.filter((s) => s.id !== id)
      return true
    } catch {
      return false
    }
  }

  // ---------------------------------------------------------------------------
  // Calendar
  // ---------------------------------------------------------------------------

  async function fetchCalendar() {
    try {
      calendarData.value = await api.get<Record<string, CalendarDay>>('/api/warroom/calendar')
    } catch {
      calendarData.value = {}
    }
  }

  // ---------------------------------------------------------------------------
  // Return
  // ---------------------------------------------------------------------------

  return {
    // State
    tasks,
    projects,
    availableTags,
    skills,
    usage,
    models,
    heartbeat,
    calendarData,
    filterProject,
    filterPriority,
    filterTags,
    loading,
    error,
    // Computed
    filteredTasks,
    tasksByStatus,
    projectsWithCounts,
    activeProjectsWithCounts,
    // Task actions
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    moveTask,
    runTask,
    addReference,
    deleteReference,
    isTaskBlocked,
    // Project actions
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    // Tag actions
    fetchTags,
    // Filter actions
    setProjectFilter,
    setPriorityFilter,
    setTagFilter,
    clearFilters,
    // Usage / model actions
    fetchUsage,
    fetchModels,
    setModel,
    // Heartbeat actions
    fetchHeartbeat,
    // Skills actions
    fetchSkills,
    toggleSkill,
    createSkill,
    deleteSkill,
    // Calendar actions
    fetchCalendar,
  }
})
