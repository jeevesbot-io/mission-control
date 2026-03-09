<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref } from 'vue'
import { useOverviewStore } from './store'
import { useWebSocket } from '@/composables/useWebSocket'
import { useApi } from '@/composables/useApi'
import PageShell from '@/components/layout/PageShell.vue'
import Badge from '@/components/ui/Badge.vue'
import McIcon from '@/components/ui/McIcon.vue'
import { getAgentIconName, getLevelIconName } from '@/composables/useIcons'

interface WarRoomStats {
  in_progress_count: number
  todo_count: number
  last_heartbeat: number | null
  active_model: string
}

const store = useOverviewStore()
const api = useApi()
const { subscribe } = useWebSocket()

const warroom = ref<WarRoomStats | null>(null)

let refreshInterval: ReturnType<typeof setInterval> | undefined
let unsubscribe: (() => void) | undefined

async function fetchAll() {
  await store.fetchOverview()
  try {
    warroom.value = await api.get<WarRoomStats>('/api/warroom/stats')
  } catch { /* silently degrade */ }
}

onMounted(async () => {
  await fetchAll()
  refreshInterval = setInterval(fetchAll, 30_000)
  unsubscribe = subscribe('overview:refresh', fetchAll)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (unsubscribe) unsubscribe()
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning, Nick'
  if (hour < 18) return 'Good afternoon, Nick'
  return 'Good evening, Nick'
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

const heartbeatAge = computed(() => {
  const last = warroom.value?.last_heartbeat
  if (!last) return 'never'
  const ms = Date.now() - last
  const min = Math.floor(ms / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const h = Math.floor(min / 60)
  return `${h}h ago`
})

const heartbeatColor = computed(() => {
  const last = warroom.value?.last_heartbeat
  if (!last) return 'var(--mc-text-muted)'
  const ms = Date.now() - last
  if (ms < 10 * 60_000) return 'var(--mc-success)'
  if (ms < 60 * 60_000) return 'var(--mc-warning)'
  return 'var(--mc-danger)'
})

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

function levelColor(level: string): string {
  const l = level.toLowerCase()
  if (l === 'error') return 'var(--mc-danger)'
  if (l === 'warning') return 'var(--mc-warning)'
  return 'var(--mc-text-muted)'
}
</script>

<template>
  <PageShell>
    <div class="ov">

      <!-- ── Header ─────────────────────────────────────────── -->
      <header class="ov__header">
        <div>
          <h2 class="ov__greeting">{{ greeting }}</h2>
          <p class="ov__sub" v-if="store.data">
            {{ store.data.agent_summary.entries_24h }} log entries today
            <span class="ov__dot">·</span>
            {{ store.data.agent_summary.unique_agents }} agents active
          </p>
          <p class="ov__sub" v-else-if="store.loading">Establishing uplink…</p>
        </div>
        <Badge v-if="store.data" :variant="healthBadge.variant" :label="healthBadge.label" />
        <Badge v-else variant="warning" label="CONNECTING…" />
      </header>

      <!-- ── Stat strip ─────────────────────────────────────── -->
      <section class="ov__stat-strip mc-stagger">
        <div class="ov__stat-card">
          <div class="ov__stat-icon" style="--ic: var(--mc-accent)">
            <McIcon name="bot" :size="16" />
          </div>
          <div class="ov__stat-body">
            <span class="ov__stat-value">{{ store.data?.agent_summary.unique_agents ?? '—' }}</span>
            <span class="ov__stat-label">Active agents</span>
          </div>
        </div>

        <div class="ov__stat-card">
          <div class="ov__stat-icon" style="--ic: var(--mc-info)">
            <McIcon name="activity" :size="16" />
          </div>
          <div class="ov__stat-body">
            <span class="ov__stat-value">{{ store.data?.agent_summary.entries_24h ?? '—' }}</span>
            <span class="ov__stat-label">Log entries today</span>
          </div>
        </div>

        <div class="ov__stat-card">
          <div class="ov__stat-icon" style="--ic: var(--mc-success)">
            <McIcon name="heart-pulse" :size="16" />
          </div>
          <div class="ov__stat-body">
            <span class="ov__stat-value">{{ store.data ? `${store.data.agent_summary.health_rate}%` : '—' }}</span>
            <span class="ov__stat-label">Health rate</span>
          </div>
        </div>

        <div class="ov__stat-card">
          <div class="ov__stat-icon" style="--ic: var(--mc-color-cyan)">
            <McIcon name="timer" :size="16" />
          </div>
          <div class="ov__stat-body">
            <span class="ov__stat-value">{{ uptimeStr }}</span>
            <span class="ov__stat-label">Uptime</span>
          </div>
        </div>
      </section>

      <!-- ── Two-column: War Room + System Health ───────────── -->
      <div class="ov__two-col">

        <!-- War Room card -->
        <div class="ov__card">
          <div class="ov__card-header">
            <McIcon name="crosshair" :size="15" class="ov__card-icon" />
            <h3 class="ov__card-title">War Room</h3>
            <a href="/warroom" class="ov__card-link">View →</a>
          </div>
          <div v-if="warroom" class="ov__warroom-grid">
            <div class="ov__wr-stat">
              <span class="ov__wr-value">{{ warroom.in_progress_count }}</span>
              <span class="ov__wr-label">In progress</span>
            </div>
            <div class="ov__wr-stat">
              <span class="ov__wr-value">{{ warroom.todo_count }}</span>
              <span class="ov__wr-label">Todo</span>
            </div>
            <div class="ov__wr-stat">
              <span class="ov__wr-value" :style="{ color: heartbeatColor }">{{ heartbeatAge }}</span>
              <span class="ov__wr-label">Last heartbeat</span>
            </div>
            <div class="ov__wr-model">
              <span class="ov__wr-label">Model</span>
              <span class="ov__wr-model-val mc-mono">{{ warroom.active_model || 'unknown' }}</span>
            </div>
          </div>
          <div v-else class="ov__empty">
            <McIcon name="loader" :size="20" />
            <span>Loading…</span>
          </div>
        </div>

        <!-- System health card -->
        <div class="ov__card">
          <div class="ov__card-header">
            <McIcon name="server" :size="15" class="ov__card-icon" />
            <h3 class="ov__card-title">System</h3>
          </div>
          <div v-if="store.data" class="ov__health-list">
            <div class="ov__health-row">
              <span class="ov__health-dot" :class="store.data.health.database ? 'ok' : 'err'" />
              <span class="ov__health-name">Database</span>
              <span class="ov__health-val mc-mono">{{ store.data.health.database ? 'Connected' : 'Disconnected' }}</span>
            </div>
            <div class="ov__health-row">
              <span class="ov__health-dot ok" />
              <span class="ov__health-name">API</span>
              <span class="ov__health-val mc-mono">v{{ store.data.health.version }}</span>
            </div>
            <div class="ov__health-row">
              <span class="ov__health-dot ok" />
              <span class="ov__health-name">Uptime</span>
              <span class="ov__health-val mc-mono">{{ uptimeStr }}</span>
            </div>
            <div class="ov__health-row">
              <span class="ov__health-dot" :class="store.data.agent_summary.warning_count === 0 ? 'ok' : 'warn'" />
              <span class="ov__health-name">Agent warnings</span>
              <span class="ov__health-val mc-mono">{{ store.data.agent_summary.warning_count }}</span>
            </div>
          </div>
          <div v-else class="ov__empty">
            <McIcon name="loader" :size="20" />
            <span>Loading…</span>
          </div>
        </div>

      </div>

      <!-- ── Recent agent activity ───────────────────────────── -->
      <div class="ov__card ov__card--full">
        <div class="ov__card-header">
          <McIcon name="scroll-text" :size="15" class="ov__card-icon" />
          <h3 class="ov__card-title">Recent Agent Activity</h3>
          <span class="ov__card-badge mc-mono">last 10</span>
        </div>

        <div v-if="!store.data?.recent_activity.length" class="ov__empty">
          <McIcon name="bot" :size="24" />
          <span>Agents standing by</span>
        </div>

        <div v-else class="ov__activity-table">
          <div
            v-for="entry in store.data!.recent_activity"
            :key="entry.id"
            class="ov__activity-row"
          >
            <McIcon
              :name="getAgentIconName(entry.agent_id)"
              :size="15"
              class="ov__act-icon"
            />
            <span class="ov__act-agent mc-mono">{{ entry.agent_id }}</span>
            <McIcon
              :name="getLevelIconName(entry.level)"
              :size="12"
              class="ov__act-level"
              :style="{ color: levelColor(entry.level) }"
            />
            <span class="ov__act-msg">{{ entry.message }}</span>
            <span class="ov__act-time mc-mono">{{ formatRelativeTime(entry.created_at) }}</span>
          </div>
        </div>
      </div>

    </div>
  </PageShell>
</template>

<style scoped>
.ov {
  max-width: 1024px;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ── Header ─────────────────────────────────────────────── */
.ov__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  animation: mc-fade-up 0.35s ease-out;
}

.ov__greeting {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.ov__sub {
  margin-top: 0.25rem;
  font-size: 0.825rem;
  color: var(--mc-text-muted);
}

.ov__dot {
  margin: 0 0.35em;
  opacity: 0.4;
}

/* ── Stat strip ──────────────────────────────────────────── */
.ov__stat-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

@media (max-width: 700px) {
  .ov__stat-strip { grid-template-columns: repeat(2, 1fr); }
}

.ov__stat-card {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 1rem 1.125rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  transition: border-color var(--mc-transition-speed), box-shadow var(--mc-transition-speed);
}

.ov__stat-card:hover {
  border-color: var(--mc-border-strong);
  box-shadow: var(--mc-shadow-sm);
}

.ov__stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--mc-radius-sm);
  background: color-mix(in srgb, var(--ic, var(--mc-accent)) 12%, transparent);
  color: var(--ic, var(--mc-accent));
  flex-shrink: 0;
}

.ov__stat-body {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.ov__stat-value {
  font-size: 1.375rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
}

.ov__stat-label {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Generic card ────────────────────────────────────────── */
.ov__card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
}

.ov__card--full {
  grid-column: 1 / -1;
}

.ov__card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.125rem;
  border-bottom: 1px solid var(--mc-border);
  background: var(--mc-bg-elevated);
}

.ov__card-icon {
  color: var(--mc-text-muted);
}

.ov__card-title {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  flex: 1;
}

.ov__card-link {
  font-size: 0.7rem;
  color: var(--mc-accent);
  text-decoration: none;
  font-weight: 500;
  transition: opacity var(--mc-transition-fast);
}

.ov__card-link:hover { opacity: 0.7; }

.ov__card-badge {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
  background: var(--mc-bg-inset);
  padding: 0.15rem 0.5rem;
  border-radius: var(--mc-radius-full);
  border: 1px solid var(--mc-border);
}

/* ── Two-column ──────────────────────────────────────────── */
.ov__two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

@media (max-width: 640px) {
  .ov__two-col { grid-template-columns: 1fr; }
}

/* ── War Room ────────────────────────────────────────────── */
.ov__warroom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}

.ov__wr-stat {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 1rem 1.125rem;
  border-right: 1px solid var(--mc-border);
  border-bottom: 1px solid var(--mc-border);
}

.ov__wr-stat:nth-child(2) { border-right: none; }

.ov__wr-model {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.875rem 1.125rem;
  grid-column: 1 / -1;
}

.ov__wr-value {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
}

.ov__wr-label {
  font-size: 0.68rem;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.ov__wr-model-val {
  font-size: 0.75rem;
  color: var(--mc-text);
  margin-top: 0.1rem;
}

/* ── System health ───────────────────────────────────────── */
.ov__health-list {
  padding: 0.5rem 0;
}

.ov__health-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 1.125rem;
  transition: background var(--mc-transition-fast);
}

.ov__health-row:hover {
  background: var(--mc-bg-hover);
}

.ov__health-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.ov__health-dot.ok {
  background: var(--mc-success);
  box-shadow: 0 0 5px color-mix(in srgb, var(--mc-success) 50%, transparent);
}

.ov__health-dot.warn {
  background: var(--mc-warning);
  box-shadow: 0 0 5px color-mix(in srgb, var(--mc-warning) 50%, transparent);
}

.ov__health-dot.err {
  background: var(--mc-danger);
  box-shadow: 0 0 5px color-mix(in srgb, var(--mc-danger) 50%, transparent);
}

.ov__health-name {
  flex: 1;
  font-size: 0.825rem;
}

.ov__health-val {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}

/* ── Activity table ──────────────────────────────────────── */
.ov__activity-table {
  display: flex;
  flex-direction: column;
}

.ov__activity-row {
  display: grid;
  grid-template-columns: 20px 140px 16px 1fr auto;
  align-items: center;
  gap: 0.625rem;
  padding: 0.6rem 1.125rem;
  border-bottom: 1px solid var(--mc-border);
  transition: background var(--mc-transition-fast);
}

.ov__activity-row:last-child {
  border-bottom: none;
}

.ov__activity-row:hover {
  background: var(--mc-bg-hover);
}

.ov__act-icon {
  color: var(--mc-text-muted);
  justify-self: center;
}

.ov__act-agent {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ov__act-level {
  justify-self: center;
}

.ov__act-msg {
  font-size: 0.8125rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ov__act-time {
  font-size: 0.68rem;
  color: var(--mc-text-muted);
  white-space: nowrap;
}

/* ── Empty state ─────────────────────────────────────────── */
.ov__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--mc-text-muted);
  font-size: 0.825rem;
}
</style>
