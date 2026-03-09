import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useApi } from '@/composables/useApi'

// ---------------------------------------------------------------------------
// Types (mirrored from warroom store — same backend)
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

export type TaskStatus = Task['status']
export type TaskPriority = Task['priority']
export type ViewMode = 'list' | 'kanban'
export type SidebarSection = 'my-tasks' | 'all' | 'by-agent' | 'by-project'
export type SortField = 'updated' | 'priority' | 'created'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const STATUS_ORDER: TaskStatus[] = ['backlog', 'todo', 'in-progress', 'done']

export const STATUS_LABELS: Record<TaskStatus, string> = {
  backlog: 'Backlog',
  todo: 'Todo',
  'in-progress': 'In Progress',
  done: 'Done',
}

export const STATUS_COLORS: Record<TaskStatus, string> = {
  backlog: 'var(--mc-text-muted)',
  todo: 'var(--mc-info)',
  'in-progress': 'var(--mc-warning)',
  done: 'var(--mc-success)',
}

export const PRIORITY_ORDER: TaskPriority[] = ['urgent', 'high', 'medium', 'low']

export const PRIORITY_LABELS: Record<TaskPriority, string> = {
  urgent: 'Urgent',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}

export const PRIORITY_COLORS: Record<TaskPriority, string> = {
  urgent: 'var(--mc-color-red)',
  high: 'var(--mc-color-orange)',
  medium: 'var(--mc-color-yellow)',
  low: 'var(--mc-text-muted)',
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useTasksStore = defineStore('tasks', () => {
  const api = useApi()

  // Data
  const tasks = ref<Task[]>([])
  const projects = ref<Project[]>([])
  const availableTags = ref<string[]>([])

  // UI state
  const selectedTaskId = ref<string | null>(null)
  const viewMode = ref<ViewMode>('list')
  const sidebarSection = ref<SidebarSection>('all')
  const sortField = ref<SortField>('updated')
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Filters
  const filters = ref<{
    project: string | null
    priority: TaskPriority | null
    status: TaskStatus | null
    agent: string | null
    tags: string[]
  }>({
    project: null,
    priority: null,
    status: null,
    agent: null,
    tags: [],
  })

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------

  const selectedTask = computed(() =>
    selectedTaskId.value ? tasks.value.find((t) => t.id === selectedTaskId.value) ?? null : null,
  )

  const filteredTasks = computed(() => {
    let result = tasks.value

    if (filters.value.project === 'untagged') {
      result = result.filter((t) => !t.project)
    } else if (filters.value.project) {
      result = result.filter((t) => t.project === filters.value.project)
    }

    if (filters.value.priority) {
      result = result.filter((t) => t.priority === filters.value.priority)
    }

    if (filters.value.status) {
      result = result.filter((t) => t.status === filters.value.status)
    }

    if (filters.value.agent) {
      result = result.filter((t) =>
        t.tags.some((tag) => tag.toLowerCase() === filters.value.agent!.toLowerCase()) ||
        t.skill?.toLowerCase() === filters.value.agent!.toLowerCase(),
      )
    }

    if (filters.value.tags.length > 0) {
      result = result.filter((t) => filters.value.tags.some((tag) => t.tags.includes(tag)))
    }

    return result
  })

  const sortedTasks = computed(() => {
    const sorted = [...filteredTasks.value]
    const priorityWeight: Record<TaskPriority, number> = { urgent: 0, high: 1, medium: 2, low: 3 }

    switch (sortField.value) {
      case 'priority':
        sorted.sort((a, b) => priorityWeight[a.priority] - priorityWeight[b.priority])
        break
      case 'created':
        sorted.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        break
      case 'updated':
      default:
        sorted.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
        break
    }
    return sorted
  })

  const tasksByStatus = computed(() => ({
    backlog: filteredTasks.value.filter((t) => t.status === 'backlog'),
    todo: filteredTasks.value.filter((t) => t.status === 'todo'),
    'in-progress': filteredTasks.value.filter((t) => t.status === 'in-progress'),
    done: filteredTasks.value.filter((t) => t.status === 'done'),
  }))

  const groupedByAgent = computed(() => {
    const map: Record<string, Task[]> = {}
    for (const t of tasks.value) {
      const agent = t.skill || 'unassigned'
      if (!map[agent]) map[agent] = []
      map[agent].push(t)
    }
    return map
  })

  const groupedByProject = computed(() => {
    const map: Record<string, Task[]> = {}
    for (const t of tasks.value) {
      const proj = t.project || 'no-project'
      if (!map[proj]) map[proj] = []
      map[proj].push(t)
    }
    return map
  })

  const agents = computed(() => {
    const set = new Set<string>()
    for (const t of tasks.value) {
      if (t.skill) set.add(t.skill)
    }
    return Array.from(set).sort()
  })

  // ---------------------------------------------------------------------------
  // Actions
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

  async function fetchProjects() {
    try {
      projects.value = await api.get<Project[]>('/api/warroom/projects')
    } catch {
      projects.value = []
    }
  }

  async function fetchTags() {
    try {
      availableTags.value = await api.get<string[]>('/api/warroom/tags')
    } catch {
      availableTags.value = []
    }
  }

  async function fetchAll() {
    await Promise.all([fetchTasks(), fetchProjects(), fetchTags()])
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
      if (selectedTaskId.value === id) selectedTaskId.value = null
      return true
    } catch {
      return false
    }
  }

  async function moveTask(id: string, newStatus: TaskStatus): Promise<void> {
    const task = tasks.value.find((t) => t.id === id)
    if (task) task.status = newStatus
    await updateTask(id, { status: newStatus })
  }

  function setFilter(key: keyof typeof filters.value, value: unknown) {
    if (key === 'tags') {
      filters.value.tags = value as string[]
    } else {
      ;(filters.value as Record<string, unknown>)[key] = value
    }
  }

  function clearFilters() {
    filters.value = { project: null, priority: null, status: null, agent: null, tags: [] }
  }

  function isTaskBlocked(task: Task): boolean {
    const blockedBy = task.blockedBy || []
    if (blockedBy.length === 0) return false
    return blockedBy.some((id) => {
      const blocker = tasks.value.find((t) => t.id === id)
      return !blocker || blocker.status !== 'done'
    })
  }

  function getProjectName(id: string | null): string {
    if (!id) return 'No Project'
    const p = projects.value.find((proj) => proj.id === id)
    return p ? p.name : id
  }

  // ---------------------------------------------------------------------------
  // Return
  // ---------------------------------------------------------------------------

  return {
    // Data
    tasks,
    projects,
    availableTags,
    // UI
    selectedTaskId,
    selectedTask,
    viewMode,
    sidebarSection,
    sortField,
    loading,
    error,
    filters,
    // Computed
    filteredTasks,
    sortedTasks,
    tasksByStatus,
    groupedByAgent,
    groupedByProject,
    agents,
    // Actions
    fetchTasks,
    fetchProjects,
    fetchTags,
    fetchAll,
    createTask,
    updateTask,
    deleteTask,
    moveTask,
    setFilter,
    clearFilters,
    isTaskBlocked,
    getProjectName,
  }
})
