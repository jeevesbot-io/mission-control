import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWarRoomStore } from './store'
import type { Task, Project } from './store'

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

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 'task-1',
    title: 'Test task',
    description: '',
    status: 'backlog',
    priority: 'medium',
    project: null,
    tags: [],
    skill: null,
    schedule: null,
    scheduledAt: null,
    references: [],
    startedAt: null,
    completedAt: null,
    result: null,
    error: null,
    pickedUp: false,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
    estimatedHours: null,
    actualHours: null,
    ...overrides,
  }
}

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: 'proj-1',
    name: 'Test Project',
    icon: 'Scaffold',
    color: 'purple',
    description: null,
    status: 'active',
    order: 1,
    ...overrides,
  }
}

describe('warroom store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  // ---------------------------------------------------------------------------
  // fetchTasks
  // ---------------------------------------------------------------------------

  describe('fetchTasks', () => {
    it('loads tasks and clears loading', async () => {
      const tasks = [makeTask({ id: '1', title: 'Alpha' }), makeTask({ id: '2', title: 'Beta', status: 'todo' })]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()

      expect(store.tasks).toHaveLength(2)
      expect(store.tasks[0]!.title).toBe('Alpha')
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useWarRoomStore()
      await store.fetchTasks()

      expect(store.tasks).toEqual([])
      expect(store.error).toBeTruthy()
      expect(store.loading).toBe(false)
    })
  })

  // ---------------------------------------------------------------------------
  // filteredTasks computed
  // ---------------------------------------------------------------------------

  describe('filteredTasks', () => {
    it('returns all tasks when no filters are set', async () => {
      const tasks = [
        makeTask({ id: '1', project: 'proj-a', tags: ['x'], priority: 'high' }),
        makeTask({ id: '2', project: 'proj-b', tags: ['y'], priority: 'low' }),
        makeTask({ id: '3', project: null, tags: [] }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()

      expect(store.filteredTasks).toHaveLength(3)
    })

    it('filters by project', async () => {
      const tasks = [
        makeTask({ id: '1', project: 'proj-a' }),
        makeTask({ id: '2', project: 'proj-b' }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()
      store.setProjectFilter('proj-a')

      expect(store.filteredTasks).toHaveLength(1)
      expect(store.filteredTasks[0]!.id).toBe('1')
    })

    it('filters by "untagged" special value (tasks with no project)', async () => {
      const tasks = [
        makeTask({ id: '1', project: 'proj-a' }),
        makeTask({ id: '2', project: null }),
        makeTask({ id: '3', project: null }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()
      store.setProjectFilter('untagged')

      expect(store.filteredTasks).toHaveLength(2)
      expect(store.filteredTasks.every((t) => !t.project)).toBe(true)
    })

    it('filters by priority', async () => {
      const tasks = [
        makeTask({ id: '1', priority: 'urgent' }),
        makeTask({ id: '2', priority: 'low' }),
        makeTask({ id: '3', priority: 'urgent' }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()
      store.setPriorityFilter('urgent')

      expect(store.filteredTasks).toHaveLength(2)
      expect(store.filteredTasks.every((t) => t.priority === 'urgent')).toBe(true)
    })

    it('filters by tags (any-match)', async () => {
      const tasks = [
        makeTask({ id: '1', tags: ['api', 'vue'] }),
        makeTask({ id: '2', tags: ['python'] }),
        makeTask({ id: '3', tags: [] }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()
      store.setTagFilter(['api'])

      expect(store.filteredTasks).toHaveLength(1)
      expect(store.filteredTasks[0]!.id).toBe('1')
    })

    it('combines project + priority filters', async () => {
      const tasks = [
        makeTask({ id: '1', project: 'proj-a', priority: 'high' }),
        makeTask({ id: '2', project: 'proj-a', priority: 'low' }),
        makeTask({ id: '3', project: 'proj-b', priority: 'high' }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()
      store.setProjectFilter('proj-a')
      store.setPriorityFilter('high')

      expect(store.filteredTasks).toHaveLength(1)
      expect(store.filteredTasks[0]!.id).toBe('1')
    })
  })

  // ---------------------------------------------------------------------------
  // tasksByStatus computed
  // ---------------------------------------------------------------------------

  describe('tasksByStatus', () => {
    it('splits tasks into four status buckets', async () => {
      const tasks = [
        makeTask({ id: '1', status: 'backlog' }),
        makeTask({ id: '2', status: 'todo' }),
        makeTask({ id: '3', status: 'in-progress' }),
        makeTask({ id: '4', status: 'done' }),
        makeTask({ id: '5', status: 'backlog' }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()

      expect(store.tasksByStatus.backlog).toHaveLength(2)
      expect(store.tasksByStatus.todo).toHaveLength(1)
      expect(store.tasksByStatus['in-progress']).toHaveLength(1)
      expect(store.tasksByStatus.done).toHaveLength(1)
    })

    it('respects active filters when splitting', async () => {
      const tasks = [
        makeTask({ id: '1', status: 'backlog', project: 'proj-a' }),
        makeTask({ id: '2', status: 'backlog', project: 'proj-b' }),
      ]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()
      store.setProjectFilter('proj-a')

      expect(store.tasksByStatus.backlog).toHaveLength(1)
      expect(store.tasksByStatus.backlog[0]!.id).toBe('1')
    })
  })

  // ---------------------------------------------------------------------------
  // moveTask
  // ---------------------------------------------------------------------------

  describe('moveTask', () => {
    it('optimistically updates status before API call', async () => {
      const tasks = [makeTask({ id: '1', status: 'backlog' })]
      mockJsonResponse(tasks)

      const store = useWarRoomStore()
      await store.fetchTasks()

      // Mock the PUT for updateTask
      mockJsonResponse({ ...tasks[0], status: 'todo' })

      const movePromise = store.moveTask('1', 'todo')

      // Optimistic update is synchronous — check immediately
      expect(store.tasks[0]!.status).toBe('todo')

      await movePromise
      expect(store.tasks[0]!.status).toBe('todo')
    })
  })

  // ---------------------------------------------------------------------------
  // clearFilters
  // ---------------------------------------------------------------------------

  describe('clearFilters', () => {
    it('resets all filter state', async () => {
      mockJsonResponse([])
      const store = useWarRoomStore()
      await store.fetchTasks()

      store.setProjectFilter('proj-a')
      store.setPriorityFilter('urgent')
      store.setTagFilter(['api'])

      store.clearFilters()

      expect(store.filterProject).toBeNull()
      expect(store.filterPriority).toBeNull()
      expect(store.filterTags).toEqual([])
    })
  })

  // ---------------------------------------------------------------------------
  // fetchProjects + projectsWithCounts
  // ---------------------------------------------------------------------------

  describe('fetchProjects', () => {
    it('loads projects', async () => {
      const projects = [
        makeProject({ id: 'p1', name: 'Alpha' }),
        makeProject({ id: 'p2', name: 'Beta', status: 'paused' }),
      ]
      mockJsonResponse(projects)

      const store = useWarRoomStore()
      await store.fetchProjects()

      expect(store.projects).toHaveLength(2)
      expect(store.projects[0]!.name).toBe('Alpha')
    })

    it('falls back to empty array on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useWarRoomStore()
      await store.fetchProjects()

      expect(store.projects).toEqual([])
    })
  })

  describe('projectsWithCounts', () => {
    it('computes task_count per project from loaded tasks', async () => {
      const tasks = [
        makeTask({ id: '1', project: 'p1' }),
        makeTask({ id: '2', project: 'p1' }),
        makeTask({ id: '3', project: 'p2' }),
      ]
      const projects = [makeProject({ id: 'p1' }), makeProject({ id: 'p2' })]

      mockJsonResponse(tasks)
      mockJsonResponse(projects)

      const store = useWarRoomStore()
      await store.fetchTasks()
      await store.fetchProjects()

      const p1 = store.projectsWithCounts.find((p) => p.id === 'p1')!
      const p2 = store.projectsWithCounts.find((p) => p.id === 'p2')!
      expect(p1.task_count).toBe(2)
      expect(p2.task_count).toBe(1)
    })

    it('activeProjectsWithCounts excludes paused/archived', async () => {
      const projects = [
        makeProject({ id: 'p1', status: 'active' }),
        makeProject({ id: 'p2', status: 'paused' }),
        makeProject({ id: 'p3', status: 'archived' }),
      ]
      mockJsonResponse([]) // tasks
      mockJsonResponse(projects)

      const store = useWarRoomStore()
      await store.fetchTasks()
      await store.fetchProjects()

      expect(store.activeProjectsWithCounts).toHaveLength(1)
      expect(store.activeProjectsWithCounts[0]!.id).toBe('p1')
    })
  })

  // ---------------------------------------------------------------------------
  // fetchCalendar
  // ---------------------------------------------------------------------------

  describe('fetchCalendar', () => {
    it('loads calendar data', async () => {
      const data = {
        '2026-01-15': { memory: true, tasks: ['Finished feature X'] },
        '2026-01-16': { memory: false, tasks: [] },
      }
      mockJsonResponse(data)

      const store = useWarRoomStore()
      await store.fetchCalendar()

      expect(store.calendarData['2026-01-15']!.memory).toBe(true)
      expect(store.calendarData['2026-01-15']!.tasks).toHaveLength(1)
      expect(store.calendarData['2026-01-16']!.memory).toBe(false)
    })

    it('falls back to empty object on failure', async () => {
      mockJsonResponse({ detail: 'error' }, 500)

      const store = useWarRoomStore()
      await store.fetchCalendar()

      expect(store.calendarData).toEqual({})
    })
  })

  // ---------------------------------------------------------------------------
  // createTask
  // ---------------------------------------------------------------------------

  describe('createTask', () => {
    it('appends new task to tasks list', async () => {
      mockJsonResponse([]) // initial fetch
      const newTask = makeTask({ id: 'new-1', title: 'Brand new task' })
      mockJsonResponse(newTask)

      const store = useWarRoomStore()
      await store.fetchTasks()
      const result = await store.createTask({ title: 'Brand new task', status: 'backlog', priority: 'medium' })

      expect(result).not.toBeNull()
      expect(store.tasks).toHaveLength(1)
      expect(store.tasks[0]!.title).toBe('Brand new task')
    })
  })

  // ---------------------------------------------------------------------------
  // deleteTask
  // ---------------------------------------------------------------------------

  describe('deleteTask', () => {
    it('removes task from list', async () => {
      const tasks = [makeTask({ id: '1' }), makeTask({ id: '2' })]
      mockJsonResponse(tasks)
      mockJsonResponse({ ok: true })

      const store = useWarRoomStore()
      await store.fetchTasks()
      await store.deleteTask('1')

      expect(store.tasks).toHaveLength(1)
      expect(store.tasks[0]!.id).toBe('2')
    })
  })
})
