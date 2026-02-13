<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useOverviewStore } from './store'
import type { UpcomingEvent, RecentActivity } from './store'
import { useWebSocket } from '@/composables/useWebSocket'
import PageShell from '@/components/layout/PageShell.vue'
import StatCard from '@/components/data/StatCard.vue'
import Badge from '@/components/ui/Badge.vue'

const store = useOverviewStore()
const { subscribe } = useWebSocket()

let refreshInterval: ReturnType<typeof setInterval> | undefined
let unsubscribe: (() => void) | undefined

onMounted(async () => {
  await store.fetchOverview()

  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(() => store.fetchOverview(), 30_000)

  // Live updates via WebSocket
  unsubscribe = subscribe('overview:refresh', () => {
    store.fetchOverview()
  })
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (unsubscribe) unsubscribe()
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning, Commander'
  if (hour < 18) return 'Good afternoon, Commander'
  return 'Good evening, Commander'
})

const healthBadge = computed(() => {
  const status = store.data?.health.status
  if (status === 'healthy') return { variant: 'success' as const, label: 'ALL SYSTEMS GO' }
  if (status === 'degraded') return { variant: 'warning' as const, label: 'DEGRADED' }
  return { variant: 'danger' as const, label: 'OFFLINE' }
})

const uptimeStr = computed(() => {
  const secs = store.data?.health.uptime_seconds ?? 0
  if (secs < 60) return `${Math.round(secs)}s`
  if (secs < 3600) return `${Math.round(secs / 60)}m`
  const hours = Math.floor(secs / 3600)
  const mins = Math.round((secs % 3600) / 60)
  return `${hours}h ${mins}m`
})

// Child colour mapping
function childColour(child: string): string {
  const lower = child.toLowerCase()
  if (lower === 'natty' || lower.includes('natty')) return 'var(--mc-info)'        // blue
  if (lower === 'elodie' || lower.includes('elodie')) return '#a78bfa'             // purple
  if (lower === 'florence' || lower.includes('florence')) return 'var(--mc-success)' // green
  return 'var(--mc-text-muted)'
}

function childLabel(child: string): string {
  // Clean up "[QE/Natty]" style prefixes — just return the child name
  const lower = child.toLowerCase()
  if (lower.includes('natty')) return 'Natty'
  if (lower.includes('elodie')) return 'Elodie'
  if (lower.includes('florence')) return 'Florence'
  return child
}

function cleanSummary(event: UpcomingEvent): string {
  // Remove "[QE/Child]" prefix from summary
  return event.summary.replace(/^\[[\w/]+\]\s*/, '')
}

function daysLabel(days: number): string {
  if (days === 0) return 'Today'
  if (days === 1) return 'Tomorrow'
  return `In ${days} days`
}

function formatEventTime(event: UpcomingEvent): string {
  if (event.event_time) {
    const [h, m] = event.event_time.split(':')
    const hour = parseInt(h!)
    const suffix = hour >= 12 ? 'PM' : 'AM'
    const displayHour = hour > 12 ? hour - 12 : hour || 12
    return `${displayHour}:${m} ${suffix}`
  }
  return 'All day'
}

function statusIcon(status: string): string {
  if (status === 'success') return '✅'
  if (status === 'error' || status === 'failed') return '❌'
  if (status === 'running') return '⏳'
  return '➖'
}

function formatRelativeTime(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = now - then
  const mins = Math.round(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}

function agentIcon(agentId: string): string {
  const lower = agentId.toLowerCase()
  if (lower.includes('matron')) return '🏥'
  if (lower.includes('archivist')) return '📜'
  if (lower.includes('jeeves')) return '🫖'
  return '🤖'
}
</script>

<template>
  <PageShell>
    <div class="overview">
      <!-- Hero section -->
      <div class="overview__hero">
        <div class="overview__hero-left">
          <h2 class="overview__greeting">{{ greeting }}</h2>
          <p class="overview__subtitle">
            <template v-if="store.data">
              {{ store.data.agent_summary.runs_24h }} agent runs today ·
              {{ store.data.upcoming_events.length }} events this week
            </template>
            <template v-else-if="store.loading">Loading systems...</template>
            <template v-else>Connecting to Mission Control...</template>
          </p>
        </div>
        <div class="overview__hero-right">
          <Badge
            v-if="store.data"
            :variant="healthBadge.variant"
            :label="healthBadge.label"
          />
          <Badge v-else variant="warning" label="CONNECTING..." />
        </div>
      </div>

      <!-- Stat cards -->
      <section class="overview__section">
        <h3 class="overview__section-title">System Telemetry</h3>
        <div class="overview__stats mc-stagger">
          <StatCard
            icon="🤖"
            :value="store.data?.stats.agents_active ?? '—'"
            label="Active Agents"
          />
          <StatCard
            icon="📅"
            :value="store.data?.stats.events_this_week ?? '—'"
            label="Events This Week"
          />
          <StatCard
            icon="📧"
            :value="store.data?.stats.emails_processed ?? '—'"
            label="Emails Processed"
          />
          <StatCard
            icon="☑️"
            :value="store.data?.stats.tasks_pending ?? '—'"
            label="Tasks Pending"
          />
          <StatCard
            icon="🎯"
            :value="store.data ? `${store.data.agent_summary.success_rate}%` : '—'"
            label="Success Rate"
          />
          <StatCard
            icon="⏱️"
            :value="uptimeStr"
            label="Uptime"
          />
        </div>
      </section>

      <!-- Two-column layout: Events + Activity -->
      <div class="overview__columns">
        <!-- Upcoming Events -->
        <section class="overview__section">
          <h3 class="overview__section-title">Upcoming Events</h3>
          <div class="overview__panel">
            <div v-if="!store.data?.upcoming_events.length" class="overview__empty">
              <span class="overview__empty-icon">🎉</span>
              <span>No events this week</span>
            </div>
            <div v-else class="overview__events-list">
              <div
                v-for="event in store.data.upcoming_events"
                :key="event.id"
                class="overview__event"
              >
                <div
                  class="overview__event-bar"
                  :style="{ background: childColour(event.child) }"
                />
                <div class="overview__event-content">
                  <div class="overview__event-top">
                    <span class="overview__event-title">{{ cleanSummary(event) }}</span>
                    <span
                      class="overview__event-child"
                      :style="{ color: childColour(event.child) }"
                    >{{ childLabel(event.child) }}</span>
                  </div>
                  <div class="overview__event-meta">
                    <span class="overview__event-date mc-mono">{{ event.event_date }}</span>
                    <span class="overview__event-time mc-mono">{{ formatEventTime(event) }}</span>
                    <span class="overview__event-days">{{ daysLabel(event.days_away) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Recent Activity -->
        <section class="overview__section">
          <h3 class="overview__section-title">Recent Agent Activity</h3>
          <div class="overview__panel">
            <div v-if="!store.data?.recent_activity.length" class="overview__empty">
              <span class="overview__empty-icon">🤖</span>
              <span>No recent agent runs</span>
            </div>
            <div v-else class="overview__activity-list">
              <div
                v-for="run in store.data.recent_activity"
                :key="run.id"
                class="overview__activity"
              >
                <span class="overview__activity-icon">{{ agentIcon(run.agent_id) }}</span>
                <div class="overview__activity-content">
                  <div class="overview__activity-top">
                    <span class="overview__activity-agent">{{ run.agent_id }}</span>
                    <span class="overview__activity-status">{{ statusIcon(run.status) }}</span>
                  </div>
                  <span class="overview__activity-summary">{{ run.summary ?? run.status }}</span>
                </div>
                <span class="overview__activity-time mc-mono">{{ formatRelativeTime(run.created_at) }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- System Health -->
      <section class="overview__section" v-if="store.data">
        <h3 class="overview__section-title">System Health</h3>
        <div class="overview__health mc-stagger">
          <div class="overview__health-item">
            <span class="overview__health-dot" :class="store.data.health.database ? 'overview__health-dot--ok' : 'overview__health-dot--err'" />
            <span>Database</span>
            <span class="overview__health-status mc-mono">{{ store.data.health.database ? 'Connected' : 'Disconnected' }}</span>
          </div>
          <div class="overview__health-item">
            <span class="overview__health-dot overview__health-dot--ok" />
            <span>API Server</span>
            <span class="overview__health-status mc-mono">v{{ store.data.health.version }}</span>
          </div>
          <div class="overview__health-item">
            <span class="overview__health-dot overview__health-dot--ok" />
            <span>Uptime</span>
            <span class="overview__health-status mc-mono">{{ uptimeStr }}</span>
          </div>
        </div>
      </section>
    </div>
  </PageShell>
</template>

<style scoped>
.overview {
  max-width: 1100px;
}

/* Hero */
.overview__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
  animation: mc-fade-up 0.4s ease-out;
}

.overview__greeting {
  font-family: var(--mc-font-display);
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.overview__subtitle {
  color: var(--mc-text-muted);
  margin-top: 0.375rem;
  font-size: 0.9375rem;
}

@media (max-width: 640px) {
  .overview__hero {
    flex-direction: column;
    gap: 0.75rem;
  }
}

/* Sections */
.overview__section {
  margin-bottom: 2.25rem;
}

.overview__section-title {
  font-family: var(--mc-font-mono);
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--mc-border);
}

/* Stat grid */
.overview__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

/* Two-column layout */
.overview__columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 800px) {
  .overview__columns {
    grid-template-columns: 1fr;
  }
}

/* Panel */
.overview__panel {
  background: var(--mc-bg-surface);
  backdrop-filter: var(--mc-glass-blur);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1rem;
  min-height: 200px;
}

/* Empty state */
.overview__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--mc-text-muted);
  font-size: 0.875rem;
}

.overview__empty-icon {
  font-size: 2rem;
  opacity: 0.6;
}

/* Events */
.overview__events-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.overview__event {
  display: flex;
  gap: 0.75rem;
  padding: 0.625rem 0.5rem;
  border-radius: var(--mc-radius-sm);
  transition: background var(--mc-transition-speed);
}

.overview__event:hover {
  background: var(--mc-bg-hover);
}

.overview__event-bar {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
  align-self: stretch;
}

.overview__event-content {
  flex: 1;
  min-width: 0;
}

.overview__event-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.overview__event-title {
  font-size: 0.85rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview__event-child {
  font-family: var(--mc-font-mono);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}

.overview__event-meta {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
  font-size: 0.7rem;
  color: var(--mc-text-muted);
}

.overview__event-days {
  font-weight: 500;
  color: var(--mc-accent);
}

/* Activity */
.overview__activity-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.overview__activity {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem;
  border-radius: var(--mc-radius-sm);
  transition: background var(--mc-transition-speed);
}

.overview__activity:hover {
  background: var(--mc-bg-hover);
}

.overview__activity-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.overview__activity-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.overview__activity-top {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.overview__activity-agent {
  font-size: 0.8rem;
  font-weight: 500;
}

.overview__activity-status {
  font-size: 0.7rem;
}

.overview__activity-summary {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview__activity-time {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

/* Health */
.overview__health {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.overview__health-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.overview__health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.overview__health-dot--ok {
  background: var(--mc-success);
  box-shadow: 0 0 6px color-mix(in srgb, var(--mc-success) 40%, transparent);
}

.overview__health-dot--err {
  background: var(--mc-danger);
  box-shadow: 0 0 6px color-mix(in srgb, var(--mc-danger) 40%, transparent);
}

.overview__health-status {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}
</style>
