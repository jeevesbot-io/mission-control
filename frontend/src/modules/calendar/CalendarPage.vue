<template>
  <div class="calendar-page">
    <div class="header">
      <h1><i class="pi pi-calendar mr-2"></i>Calendar</h1>
      <p class="subtitle">Scheduled tasks, cron jobs, and upcoming work</p>
    </div>

    <div v-if="error" class="error-banner">
      <i class="pi pi-exclamation-triangle mr-2"></i>
      {{ error }}
    </div>

    <div class="calendar-controls mb-4">
      <div class="controls-left">
        <Button
          label="Today"
          icon="pi pi-calendar"
          @click="goToToday"
          :outlined="true"
          size="small"
        />
        <SelectButton
          v-model="viewMode"
          :options="viewModes"
          optionLabel="label"
          optionValue="value"
          size="small"
        />
        <Dropdown
          v-model="daysAhead"
          :options="daysOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Time range"
          size="small"
          @change="refresh"
        />
      </div>
      <Button
        label="Refresh"
        icon="pi pi-refresh"
        @click="refresh"
        :loading="loading"
        :outlined="true"
        size="small"
      />
    </div>

    <div class="calendar-content">
      <!-- Timeline View -->
      <Panel v-if="viewMode === 'timeline'" header="Upcoming Events" class="timeline-panel mb-4">
        <ProgressSpinner v-if="loading" class="loading-spinner" />
        <Timeline
          v-else-if="events.length > 0"
          :value="events"
          align="alternate"
          class="customized-timeline"
        >
          <template #marker="slotProps">
            <span
              class="event-marker"
              :class="`event-marker-${slotProps.item.type}`"
            >
              <i :class="getEventIcon(slotProps.item)"></i>
            </span>
          </template>
          <template #content="slotProps">
            <Card class="event-card">
              <template #title>
                <div class="event-title">
                  {{ slotProps.item.title }}
                  <Tag
                    :value="slotProps.item.type"
                    :severity="getTypeSeverity(slotProps.item.type)"
                    class="ml-2"
                  />
                </div>
              </template>
              <template #subtitle>
                <div class="event-time">
                  <i class="pi pi-clock mr-1"></i>
                  {{ formatDateTime(slotProps.item.start) }}
                  <span v-if="slotProps.item.agent" class="ml-2">
                    <i class="pi pi-user mr-1"></i>
                    {{ slotProps.item.agent }}
                  </span>
                </div>
              </template>
              <template #content>
                <p v-if="slotProps.item.description" class="event-description">
                  {{ slotProps.item.description }}
                </p>
                <div v-if="slotProps.item.metadata?.runCount !== undefined" class="metadata">
                  <span class="metadata-item">
                    <i class="pi pi-replay mr-1"></i>
                    {{ slotProps.item.metadata.runCount }} runs
                  </span>
                </div>
              </template>
            </Card>
          </template>
        </Timeline>
        <div v-else class="no-events">
          <i class="pi pi-calendar-times mb-3" style="font-size: 3rem; opacity: 0.5"></i>
          <p>No upcoming events scheduled</p>
        </div>
      </Panel>

      <!-- Grid View -->
      <Panel v-if="viewMode === 'grid'" header="Upcoming Events" class="grid-panel mb-4">
        <ProgressSpinner v-if="loading" class="loading-spinner" />
        <div v-else-if="events.length > 0" class="events-grid">
          <Card v-for="event in events" :key="event.id" class="event-grid-card">
            <template #header>
              <div class="event-grid-header">
                <span
                  class="event-icon"
                  :class="`event-icon-${event.type}`"
                >
                  <i :class="getEventIcon(event)"></i>
                </span>
                <Tag
                  :value="event.type"
                  :severity="getTypeSeverity(event.type)"
                  class="ml-2"
                />
              </div>
            </template>
            <template #title>
              {{ event.title }}
            </template>
            <template #subtitle>
              <div class="event-grid-time">
                <i class="pi pi-clock mr-1"></i>
                {{ formatDateTime(event.start) }}
              </div>
            </template>
            <template #content>
              <p v-if="event.description" class="event-description">
                {{ event.description }}
              </p>
              <div v-if="event.agent" class="agent-badge">
                <i class="pi pi-user mr-1"></i>
                {{ event.agent }}
              </div>
            </template>
          </Card>
        </div>
        <div v-else class="no-events">
          <i class="pi pi-calendar-times mb-3" style="font-size: 3rem; opacity: 0.5"></i>
          <p>No upcoming events scheduled</p>
        </div>
      </Panel>

      <!-- Weekly Grid View -->
      <Panel v-if="viewMode === 'week'" header="Weekly View" class="week-panel mb-4">
        <ProgressSpinner v-if="loading" class="loading-spinner" />
        <div v-else class="week-grid">
          <div v-for="day in weekDays" :key="day.label" class="week-day-col">
            <div class="week-day-header" :class="{ 'is-today': day.isToday }">
              <span class="week-day-name">{{ day.dayName }}</span>
              <span class="week-day-date">{{ day.label }}</span>
            </div>
            <div class="week-day-events">
              <div v-if="day.events.length === 0" class="week-no-events">-</div>
              <Card v-for="event in day.events" :key="event.id" class="week-event-card">
                <template #content>
                  <div class="week-event-title">
                    <i :class="getEventIcon(event)" class="mr-1"></i>
                    {{ event.title }}
                  </div>
                  <div class="week-event-time">{{ formatDateTime(event.start) }}</div>
                </template>
              </Card>
            </div>
          </div>
        </div>
      </Panel>

      <!-- Cron Jobs List (gateway) -->
      <Panel v-if="cronJobs.length > 0" header="Gateway Cron Jobs" class="cron-panel mb-4">
        <DataTable
          :value="cronJobs"
          :loading="loading"
          stripedRows
          size="small"
          :paginator="cronJobs.length > 10"
          :rows="10"
        >
          <Column field="name" header="Name" sortable>
            <template #body="slotProps">
              {{ slotProps.data.name || 'Unnamed Job' }}
            </template>
          </Column>
          <Column field="schedule.kind" header="Schedule" sortable>
            <template #body="slotProps">
              <Tag :value="slotProps.data.schedule.kind" />
              <span class="ml-2 schedule-detail">
                {{ formatSchedule(slotProps.data.schedule) }}
              </span>
            </template>
          </Column>
          <Column field="sessionTarget" header="Target" sortable>
            <template #body="slotProps">
              <Tag
                :value="slotProps.data.sessionTarget"
                :severity="slotProps.data.sessionTarget === 'main' ? 'info' : 'secondary'"
              />
            </template>
          </Column>
          <Column field="enabled" header="Status" sortable>
            <template #body="slotProps">
              <Tag
                :value="slotProps.data.enabled ? 'Enabled' : 'Disabled'"
                :severity="slotProps.data.enabled ? 'success' : 'danger'"
              />
            </template>
          </Column>
          <Column field="runCount" header="Runs" sortable />
          <Column field="nextRunAt" header="Next Run" sortable>
            <template #body="slotProps">
              {{ slotProps.data.nextRunAt ? formatDateTime(slotProps.data.nextRunAt) : 'N/A' }}
            </template>
          </Column>
        </DataTable>
      </Panel>

      <!-- Agent Cron Jobs -->
      <Panel header="Agent Cron Jobs" class="cron-panel">
        <DataTable
          :value="agentCronJobs"
          :loading="loading"
          stripedRows
          size="small"
          :paginator="agentCronJobs.length > 10"
          :rows="10"
        >
          <Column field="agent_id" header="Agent" sortable />
          <Column field="schedule" header="Schedule" sortable />
          <Column field="enabled" header="Status" sortable>
            <template #body="slotProps">
              <Tag
                :value="slotProps.data.enabled ? 'Enabled' : 'Disabled'"
                :severity="slotProps.data.enabled ? 'success' : 'danger'"
              />
            </template>
          </Column>
          <Column field="last_run" header="Last Run" sortable>
            <template #body="slotProps">
              {{ slotProps.data.last_run ? formatDateTime(slotProps.data.last_run) : 'Never' }}
            </template>
          </Column>
          <Column field="next_run" header="Next Run" sortable>
            <template #body="slotProps">
              {{ slotProps.data.next_run ? formatDateTime(slotProps.data.next_run) : 'N/A' }}
            </template>
          </Column>
        </DataTable>
      </Panel>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useCalendarStore } from './store'
import Button from 'primevue/button'
import Panel from 'primevue/panel'
import Timeline from 'primevue/timeline'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ProgressSpinner from 'primevue/progressspinner'
import SelectButton from 'primevue/selectbutton'
import Dropdown from 'primevue/dropdown'
import type { components } from '@/types/api'

type CalendarEvent = components['schemas']['CalendarEvent']
type CronSchedule = components['schemas']['CronSchedule']

const store = useCalendarStore()

const events = computed(() => store.events)
const cronJobs = computed(() => store.cronJobs)
const agentCronJobs = computed(() => store.agentCronJobs)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

const viewMode = ref('timeline')
const viewModes = [
  { label: 'Timeline', value: 'timeline' },
  { label: 'Grid', value: 'grid' },
  { label: 'Week', value: 'week' },
]

const daysAhead = ref(14)
const daysOptions = [
  { label: '7 days', value: 7 },
  { label: '14 days', value: 14 },
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
]

onMounted(() => {
  store.fetchCalendar(daysAhead.value)
  store.fetchAgentsCron()
})

const weekDays = computed(() => {
  const now = new Date()
  const startOfWeek = new Date(now)
  startOfWeek.setDate(now.getDate() - now.getDay()) // Start on Sunday
  const days = []
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  for (let i = 0; i < 7; i++) {
    const d = new Date(startOfWeek)
    d.setDate(startOfWeek.getDate() + i)
    const dateStr = d.toISOString().slice(0, 10)
    const isToday = dateStr === now.toISOString().slice(0, 10)
    const dayEvents = events.value.filter((e) => {
      const eventDate = new Date(e.start).toISOString().slice(0, 10)
      return eventDate === dateStr
    })
    days.push({
      label: d.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' }),
      dayName: dayNames[i],
      isToday,
      events: dayEvents,
    })
  }
  return days
})

function refresh() {
  store.fetchCalendar(daysAhead.value)
}

function goToToday() {
  // Scroll to today's events
  store.fetchCalendar(daysAhead.value)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function getEventIcon(event: CalendarEvent): string {
  const iconMap = {
    cron: 'pi pi-clock',
    task: 'pi pi-check-square',
    reminder: 'pi pi-bell',
  }
  return iconMap[event.type] || 'pi pi-calendar'
}

function getTypeSeverity(type: string): string {
  const severityMap: Record<string, string> = {
    cron: 'info',
    task: 'warning',
    reminder: 'success',
  }
  return severityMap[type] || 'secondary'
}

function formatDateTime(dateStr: string | Date): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  // Relative time for near future
  if (diffMins < 60 && diffMins >= 0) {
    return `in ${diffMins} minute${diffMins !== 1 ? 's' : ''}`
  } else if (diffHours < 24 && diffHours >= 0) {
    return `in ${diffHours} hour${diffHours !== 1 ? 's' : ''}`
  } else if (diffDays < 7 && diffDays >= 0) {
    return `in ${diffDays} day${diffDays !== 1 ? 's' : ''}`
  }

  // Absolute time
  return date.toLocaleString('en-GB', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatSchedule(schedule: CronSchedule): string {
  if (schedule.kind === 'at' && schedule.at) {
    return `at ${formatDateTime(schedule.at)}`
  } else if (schedule.kind === 'every' && schedule.everyMs) {
    const mins = schedule.everyMs / 60000
    if (mins >= 60) {
      const hours = mins / 60
      return `every ${hours.toFixed(1)}h`
    }
    return `every ${mins}m`
  } else if (schedule.kind === 'cron' && schedule.expr) {
    return schedule.expr
  }
  return 'Unknown'
}
</script>

<style scoped>
.calendar-page {
  padding: 2rem;
}

.header {
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
}

.subtitle {
  color: var(--text-color-secondary);
  margin: 0;
}

.error-banner {
  background: var(--red-100);
  color: var(--red-900);
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.calendar-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.controls-left {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.calendar-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  margin: 2rem auto;
}

.no-events {
  text-align: center;
  padding: 3rem;
  color: var(--text-color-secondary);
}

/* Timeline Customization */
.customized-timeline :deep(.p-timeline-event-marker) {
  border: 0;
  padding: 0;
}

.event-marker {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  color: white;
  font-size: 1.2rem;
}

.event-marker-cron {
  background: var(--blue-500);
}

.event-marker-task {
  background: var(--orange-500);
}

.event-marker-reminder {
  background: var(--green-500);
}

.event-card {
  margin-top: 0.5rem;
}

.event-title {
  display: flex;
  align-items: center;
}

.event-time {
  display: flex;
  align-items: center;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.event-description {
  margin: 0.5rem 0 0 0;
  color: var(--text-color-secondary);
}

.metadata {
  margin-top: 0.5rem;
  display: flex;
  gap: 1rem;
}

.metadata-item {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}

.schedule-detail {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

/* Grid View */
.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.event-grid-card {
  height: 100%;
}

.event-grid-header {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: var(--surface-50);
}

.event-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  color: white;
  font-size: 1.2rem;
}

.event-icon-cron {
  background: var(--blue-500);
}

.event-icon-task {
  background: var(--orange-500);
}

.event-icon-reminder {
  background: var(--green-500);
}

.event-grid-time {
  display: flex;
  align-items: center;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.agent-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  background: var(--surface-100);
  border-radius: 6px;
  font-size: 0.85rem;
  margin-top: 1rem;
}

/* Weekly Grid View */
.week-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.5rem;
  min-height: 300px;
}

.week-day-col {
  display: flex;
  flex-direction: column;
  background: var(--surface-50);
  border-radius: 6px;
  overflow: hidden;
}

.week-day-header {
  padding: 0.75rem 0.5rem;
  text-align: center;
  border-bottom: 2px solid var(--surface-200);
  font-weight: 600;
}

.week-day-header.is-today {
  background: rgba(59, 130, 246, 0.1);
  border-bottom-color: var(--blue-500);
}

.week-day-name {
  display: block;
  font-size: 0.75rem;
  color: var(--text-color-secondary);
  text-transform: uppercase;
}

.week-day-date {
  display: block;
  font-size: 0.9rem;
}

.week-day-events {
  padding: 0.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.week-no-events {
  text-align: center;
  color: var(--text-color-secondary);
  padding: 1rem 0;
}

.week-event-card {
  font-size: 0.8rem;
}

.week-event-title {
  font-weight: 600;
  font-size: 0.78rem;
  display: flex;
  align-items: center;
}

.week-event-time {
  font-size: 0.72rem;
  color: var(--text-color-secondary);
  margin-top: 0.25rem;
}
</style>
