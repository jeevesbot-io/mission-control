import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

interface CalendarEvent {
  id: string
  summary: string
  start_date: string | null
  start_datetime: string | null
  end_date: string | null
  end_datetime: string | null
  all_day: boolean
  child: string | null
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

export type { CalendarEvent, SchoolEmail, TodoistTask, SchoolStats }

export const useSchoolStore = defineStore('school', () => {
  const api = useApi()

  const calendarEvents = ref<CalendarEvent[]>([])
  const calendarWindowStart = ref('')
  const calendarWindowEnd = ref('')
  const emails = ref<SchoolEmail[]>([])
  const tasks = ref<TodoistTask[]>([])
  const stats = ref<SchoolStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCalendar() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{
        events: CalendarEvent[]
        total: number
        window_start: string
        window_end: string
      }>('/api/school/calendar?days=7')
      calendarEvents.value = data.events
      calendarWindowStart.value = data.window_start
      calendarWindowEnd.value = data.window_end
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load calendar'
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
    calendarEvents,
    calendarWindowStart,
    calendarWindowEnd,
    emails,
    tasks,
    stats,
    loading,
    error,
    fetchCalendar,
    fetchEmails,
    fetchTasks,
    fetchStats,
  }
})
