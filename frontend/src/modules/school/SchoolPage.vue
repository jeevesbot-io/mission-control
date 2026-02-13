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
  if (activeTab.value === 'events') store.fetchEvents()
  else if (activeTab.value === 'emails') store.fetchEmails()
  else store.fetchTasks()
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function priorityLabel(p: number): string {
  if (p >= 4) return 'Urgent'
  if (p === 3) return 'High'
  if (p === 2) return 'Medium'
  return 'Low'
}

function priorityClass(p: number): string {
  if (p >= 4) return 'school__priority--urgent'
  if (p === 3) return 'school__priority--high'
  if (p === 2) return 'school__priority--medium'
  return 'school__priority--low'
}
</script>

<template>
  <PageShell>
    <div class="school">
      <div class="school__header">
        <h2 class="school__title">School Dashboard</h2>
        <p class="school__subtitle">Events, emails, and tasks in one place</p>
      </div>

      <!-- Stats -->
      <section class="school__section" v-if="store.stats">
        <h3 class="school__section-title">Overview</h3>
        <div class="school__stats mc-stagger">
          <StatCard icon="&#x1f4c5;" :value="store.stats.upcoming_events" label="Upcoming Events" />
          <StatCard icon="&#x2709;&#xfe0f;" :value="store.stats.unread_emails" label="Unread Emails" />
          <StatCard icon="&#x2611;&#xfe0f;" :value="store.stats.pending_tasks" label="Pending Tasks" />
          <StatCard icon="&#x2705;" :value="store.stats.completed_today" label="Completed Today" />
        </div>
      </section>

      <!-- Tabs -->
      <div class="school__tabs">
        <button
          class="school__tab"
          :class="{ 'school__tab--active': activeTab === 'events' }"
          @click="activeTab = 'events'"
        >
          Events
          <span v-if="store.stats" class="school__tab-count">{{ store.stats.upcoming_events }}</span>
        </button>
        <button
          class="school__tab"
          :class="{ 'school__tab--active': activeTab === 'emails' }"
          @click="activeTab = 'emails'"
        >
          Emails
          <span v-if="store.stats" class="school__tab-count">{{ store.stats.unread_emails }}</span>
        </button>
        <button
          class="school__tab"
          :class="{ 'school__tab--active': activeTab === 'tasks' }"
          @click="activeTab = 'tasks'"
        >
          Tasks
          <span v-if="store.stats" class="school__tab-count">{{ store.stats.pending_tasks }}</span>
        </button>
      </div>

      <!-- Events Panel -->
      <div v-if="activeTab === 'events'" class="school__panel">
        <div v-if="store.events.length === 0 && !store.loading" class="school__empty">
          No upcoming events
        </div>
        <div class="school__list mc-stagger">
          <div
            v-for="event in store.events"
            :key="event.id"
            class="school__event"
          >
            <div class="school__event-time">
              <span class="mc-mono">{{ formatDate(event.start_time) }}</span>
              <span v-if="event.all_day" class="school__badge">All Day</span>
            </div>
            <div class="school__event-title">{{ event.title }}</div>
            <div v-if="event.location" class="school__event-location">
              <i class="pi pi-map-marker" /> {{ event.location }}
            </div>
            <div v-if="event.description" class="school__event-desc">
              {{ event.description }}
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
            :class="{ 'school__email--unread': !email.is_read }"
          >
            <div class="school__email-header">
              <span class="school__email-sender">{{ email.sender }}</span>
              <span class="school__email-date mc-mono">{{ formatShortDate(email.received_at) }}</span>
            </div>
            <div class="school__email-subject">{{ email.subject }}</div>
            <div class="school__email-preview">{{ email.preview }}</div>
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
            :class="{ 'school__task--done': task.is_completed }"
          >
            <div class="school__task-check">
              <span v-if="task.is_completed">&#x2705;</span>
              <span v-else>&#x2b1c;</span>
            </div>
            <div class="school__task-body">
              <div class="school__task-content">{{ task.content }}</div>
              <div class="school__task-meta">
                <span
                  class="school__priority"
                  :class="priorityClass(task.priority)"
                >{{ priorityLabel(task.priority) }}</span>
                <span v-if="task.due_date" class="mc-mono">Due: {{ task.due_date }}</span>
                <span v-if="task.project_name" class="school__task-project">{{ task.project_name }}</span>
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

/* Sections */
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

/* Tabs */
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

.school__tab-count {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
}

/* Panel */
.school__panel {
  min-height: 200px;
}

.school__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Events */
.school__event {
  padding: 1rem 1.25rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  transition: border-color var(--mc-transition-speed);
}

.school__event:hover {
  border-color: var(--mc-border-strong);
}

.school__event-time {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-accent);
  margin-bottom: 0.25rem;
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

.school__event-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.school__event-location {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 0.25rem;
}

.school__event-desc {
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  line-height: 1.4;
}

/* Emails */
.school__email {
  padding: 1rem 1.25rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  transition: border-color var(--mc-transition-speed);
}

.school__email:hover {
  border-color: var(--mc-border-strong);
}

.school__email--unread {
  border-left: 3px solid var(--mc-accent);
}

.school__email-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.school__email-sender {
  font-size: 0.85rem;
  font-weight: 500;
}

.school__email-date {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}

.school__email-subject {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.school__email-preview {
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Tasks */
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

.school__task--done {
  opacity: 0.55;
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

.school__priority {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
  text-transform: uppercase;
}

.school__priority--urgent {
  color: var(--mc-danger);
  background: color-mix(in srgb, var(--mc-danger) 10%, transparent);
}

.school__priority--high {
  color: var(--mc-warning);
  background: color-mix(in srgb, var(--mc-warning) 10%, transparent);
}

.school__priority--medium {
  color: var(--mc-info);
  background: color-mix(in srgb, var(--mc-info) 10%, transparent);
}

.school__priority--low {
  color: var(--mc-text-muted);
  background: var(--mc-bg-elevated);
}

.school__task-project {
  background: var(--mc-bg-elevated);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

/* Empty / Loading / Error */
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
