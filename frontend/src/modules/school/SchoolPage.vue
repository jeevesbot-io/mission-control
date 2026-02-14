<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useSchoolStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'
import StatCard from '@/components/data/StatCard.vue'

const store = useSchoolStore()
const activeTab = ref<'events' | 'emails' | 'tasks'>('events')

onMounted(() => {
  store.fetchStats()
  loadTab()
})

watch(activeTab, () => {
  loadTab()
})

function loadTab() {
  if (activeTab.value === 'events') store.fetchCalendar()
  else if (activeTab.value === 'emails') store.fetchEmails()
  else store.fetchTasks()
}

function childColour(child: string | null): string {
  if (!child) return 'var(--mc-text-muted)'
  const lower = child.toLowerCase()
  if (lower.includes('natty')) return 'var(--mc-info)'
  if (lower.includes('elodie')) return '#a78bfa'
  if (lower.includes('florence')) return 'var(--mc-success)'
  return 'var(--mc-text-muted)'
}

function formatEventDate(event: { start_date: string | null; start_datetime: string | null; all_day: boolean }): string {
  if (event.all_day && event.start_date) {
    return new Date(event.start_date + 'T00:00:00').toLocaleString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    })
  }
  if (event.start_datetime) {
    return new Date(event.start_datetime).toLocaleString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }
  return ''
}

function formatTime(event: { start_datetime: string | null; end_datetime: string | null; all_day: boolean }): string {
  if (event.all_day) return 'All day'
  if (!event.start_datetime) return ''
  const start = new Date(event.start_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  if (event.end_datetime) {
    const end = new Date(event.end_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
    return `${start} – ${end}`
  }
  return start
}

function formatDateTime(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function windowLabel(): string {
  if (!store.calendarWindowStart || !store.calendarWindowEnd) return 'Next 7 days'
  const fmt = (iso: string) => new Date(iso + 'T00:00:00').toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
  })
  return `${fmt(store.calendarWindowStart)} – ${fmt(store.calendarWindowEnd)}`
}
</script>

<template>
  <PageShell>
    <div class="school">
      <div class="school__header">
        <h2 class="school__title">School &amp; Family</h2>
        <p class="school__subtitle">Calendar, emails, and tasks</p>
      </div>

      <!-- Stats -->
      <section class="school__section" v-if="store.stats">
        <h3 class="school__section-title">Overview</h3>
        <div class="school__stats mc-stagger">
          <StatCard icon="📅" :value="store.stats.upcoming_events" label="Events (7 days)" />
          <StatCard icon="✉️" :value="store.stats.total_emails" label="Total Emails" />
          <StatCard icon="☑️" :value="store.stats.total_tasks" label="Tasks" />
        </div>
      </section>

      <!-- Tabs -->
      <div class="school__tabs">
        <button
          class="school__tab"
          :class="{ 'school__tab--active': activeTab === 'events' }"
          @click="activeTab = 'events'"
        >
          Calendar
        </button>
        <button
          class="school__tab"
          :class="{ 'school__tab--active': activeTab === 'emails' }"
          @click="activeTab = 'emails'"
        >
          Emails
        </button>
        <button
          class="school__tab"
          :class="{ 'school__tab--active': activeTab === 'tasks' }"
          @click="activeTab = 'tasks'"
        >
          Tasks
        </button>
      </div>

      <!-- Calendar Events Panel -->
      <div v-if="activeTab === 'events'" class="school__panel">
        <div class="school__window-label mc-mono">{{ windowLabel() }}</div>

        <div v-if="store.calendarEvents.length === 0 && !store.loading" class="school__empty">
          No events in the next 7 days
        </div>
        <div class="school__list mc-stagger">
          <div
            v-for="event in store.calendarEvents"
            :key="event.id"
            class="school__event"
          >
            <div
              class="school__event-bar"
              :style="{ background: childColour(event.child) }"
            />
            <div class="school__event-body">
              <div class="school__event-top">
                <span class="school__event-title">{{ event.summary }}</span>
                <span
                  v-if="event.child"
                  class="school__event-child"
                  :style="{ color: childColour(event.child) }"
                >{{ event.child }}</span>
              </div>
              <div class="school__event-meta">
                <span class="mc-mono">{{ formatEventDate(event) }}</span>
                <span class="mc-mono school__event-time">{{ formatTime(event) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Emails Panel -->
      <div v-if="activeTab === 'emails'" class="school__panel">
        <div v-if="store.emails.length === 0 && !store.loading" class="school__empty">
          No emails found
        </div>
        <div class="school__list mc-stagger">
          <div
            v-for="email in store.emails"
            :key="email.id"
            class="school__email"
          >
            <div
              class="school__email-bar"
              :style="{ background: childColour(email.child) }"
            />
            <div class="school__email-body">
              <div class="school__email-header">
                <span class="school__email-subject">{{ email.subject }}</span>
                <span class="school__email-date mc-mono">{{ formatDateTime(email.processed_at) }}</span>
              </div>
              <div class="school__email-sender">{{ email.sender }}</div>
              <div v-if="email.preview" class="school__email-preview">{{ email.preview }}</div>
              <div class="school__email-tags">
                <span
                  v-if="email.child"
                  class="school__email-child"
                  :style="{ color: childColour(email.child) }"
                >{{ email.child }}</span>
                <span v-if="email.school_id" class="school__badge">{{ email.school_id }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tasks Panel -->
      <div v-if="activeTab === 'tasks'" class="school__panel">
        <div v-if="store.tasks.length === 0 && !store.loading" class="school__empty">
          No tasks found
        </div>
        <div class="school__list mc-stagger">
          <div
            v-for="task in store.tasks"
            :key="task.id"
            class="school__task"
          >
            <div class="school__task-check">⬜</div>
            <div class="school__task-body">
              <div class="school__task-content">{{ task.content }}</div>
              <div class="school__task-meta">
                <span v-if="task.due_date" class="mc-mono">Due: {{ task.due_date }}</span>
                <span v-if="task.description" class="school__task-desc">{{ task.description }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" class="school__loading">
        <i class="pi pi-spin pi-spinner" /> Loading...
      </div>

      <!-- Error -->
      <div v-if="store.error" class="school__error">
        <i class="pi pi-exclamation-triangle" />
        {{ store.error }}
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.school {
  max-width: 960px;
}

.school__header {
  margin-bottom: 1.5rem;
}

.school__title {
  font-family: var(--mc-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.school__subtitle {
  color: var(--mc-text-muted);
  font-size: 0.9rem;
}

.school__section {
  margin-bottom: 2rem;
}

.school__section-title {
  font-family: var(--mc-font-display);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mc-text-muted);
  margin-bottom: 0.75rem;
}

.school__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.school__tabs {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--mc-border);
}

.school__tab {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.75rem 1.25rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-body);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}

.school__tab:hover {
  color: var(--mc-text);
}

.school__tab--active {
  color: var(--mc-accent);
  border-bottom-color: var(--mc-accent);
}

.school__panel {
  min-height: 200px;
}

.school__window-label {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.75rem;
  padding: 0.35rem 0.75rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  display: inline-block;
}

.school__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.school__event {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  transition: border-color var(--mc-transition-speed);
}

.school__event:hover {
  border-color: var(--mc-border-strong);
}

.school__event-bar {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
  align-self: stretch;
}

.school__event-body {
  flex: 1;
  min-width: 0;
}

.school__event-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.school__event-title {
  font-weight: 600;
}

.school__event-child {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}

.school__event-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
}

.school__event-time {
  font-size: 0.75rem;
}

.school__badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
  text-transform: uppercase;
}

.school__email {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  transition: border-color var(--mc-transition-speed);
}

.school__email:hover {
  border-color: var(--mc-border-strong);
}

.school__email-bar {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
  align-self: stretch;
}

.school__email-body {
  flex: 1;
  min-width: 0;
}

.school__email-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.school__email-subject {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.school__email-date {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  flex-shrink: 0;
}

.school__email-sender {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.school__email-preview {
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 0.25rem;
}

.school__email-tags {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.school__email-child {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.school__task {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  transition: border-color var(--mc-transition-speed);
}

.school__task:hover {
  border-color: var(--mc-border-strong);
}

.school__task-check {
  font-size: 1rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.school__task-body {
  flex: 1;
  min-width: 0;
}

.school__task-content {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.school__task-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}

.school__task-desc {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.school__empty {
  text-align: center;
  padding: 2rem;
  color: var(--mc-text-muted);
}

.school__loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--mc-text-muted);
  font-size: 0.85rem;
  margin-top: 1rem;
}

.school__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-danger);
  font-size: 0.85rem;
  margin-top: 1rem;
}
</style>
