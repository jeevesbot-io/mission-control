import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

interface SchoolEvent {
  id: number
  child: string | null
  summary: string
  description: string | null
  event_date: string | null
  event_end_date: string | null
  event_time: string | null
  school_id: string | null
}

interface SchoolEmail {
  id: number
  email_id: string
  subject: string | null
  sender: string | null
  child: string | null
  school_id: string | null
  preview: string | null
  processed_at: string | null
}

interface TodoistTask {
  id: string
  content: string
  description: string | null
  due_date: string | null
  todoist_id: string | null
  created_at: string | null
}

interface SchoolStats {
  upcoming_events: number
  total_emails: number
  total_tasks: number
}

export type { SchoolEvent, SchoolEmail, TodoistTask, SchoolStats }

export const useSchoolStore = defineStore('school', () => {
  const api = useApi()

  const events = ref<SchoolEvent[]>([])
  const emails = ref<SchoolEmail[]>([])
  const tasks = ref<TodoistTask[]>([])
  const stats = ref<SchoolStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchEvents() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ events: SchoolEvent[]; total: number }>('/api/school/events')
      events.value = data.events
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load events'
    } finally {
      loading.value = false
    }
  }

  async function fetchEmails() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ emails: SchoolEmail[]; total: number }>('/api/school/emails')
      emails.value = data.emails
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load emails'
    } finally {
      loading.value = false
    }
  }

  async function fetchTasks() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ tasks: TodoistTask[]; total: number }>('/api/school/tasks')
      tasks.value = data.tasks
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load tasks'
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      stats.value = await api.get<SchoolStats>('/api/school/stats')
    } catch {
      stats.value = null
    }
  }

  return {
    events,
    emails,
    tasks,
    stats,
    loading,
    error,
    fetchEvents,
    fetchEmails,
    fetchTasks,
    fetchStats,
  }
})
