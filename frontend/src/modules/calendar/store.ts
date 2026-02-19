import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import type { components } from '@/types/api'

type CalendarEvent = components['schemas']['CalendarEvent']
type CronJob = components['schemas']['CronJob']

export const useCalendarStore = defineStore('calendar', () => {
  const api = useApi()
  const events = ref<CalendarEvent[]>([])
  const cronJobs = ref<CronJob[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCalendar(daysAhead = 14) {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ events: CalendarEvent[]; cronJobs: CronJob[] }>(
        `/api/calendar?days_ahead=${daysAhead}`,
      )
      events.value = data.events || []
      cronJobs.value = data.cronJobs || []
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error fetching calendar:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchCronJobs() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ jobs: CronJob[] }>('/api/calendar/jobs')
      cronJobs.value = data.jobs || []
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error fetching cron jobs:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    events,
    cronJobs,
    loading,
    error,
    fetchCalendar,
    fetchCronJobs,
  }
})
