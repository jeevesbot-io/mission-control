import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { components } from '@/types/api'

type CalendarEvent = components['schemas']['CalendarEvent']
type CronJob = components['schemas']['CronJob']

export const useCalendarStore = defineStore('calendar', () => {
  const events = ref<CalendarEvent[]>([])
  const cronJobs = ref<CronJob[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCalendar(daysAhead = 14) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({
        days_ahead: daysAhead.toString(),
      })
      const response = await fetch(`/api/calendar?${params}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch calendar: ${response.statusText}`)
      }
      const data = await response.json()
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
      const response = await fetch('/api/calendar/jobs')
      if (!response.ok) {
        throw new Error(`Failed to fetch cron jobs: ${response.statusText}`)
      }
      const data = await response.json()
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
