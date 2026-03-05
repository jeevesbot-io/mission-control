<template>
  <PageShell><div class="office-page">
    <div class="header">
      <div>
        <h1><McIcon name="building" :size="24" class="mr-2" />Office View</h1>
        <p class="subtitle">Real-time agent activity and workstations</p>
      </div>
      <Button
        label="Refresh"
        icon="pi pi-refresh"
        @click="refresh"
        :loading="loading"
        :outlined="true"
      />
    </div>

    <div v-if="error" class="error-banner">
      <McIcon name="alert-triangle" :size="16" class="mr-2" />
      {{ error }}
    </div>

    <!-- Stats -->
    <div class="stats-bar mb-4">
      <Card class="stat-card">
        <template #content>
          <McIcon name="bot" :size="32" class="stat-icon" />
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_agents || 0 }}</div>
            <div class="stat-label">Total Agents</div>
          </div>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
          <McIcon name="circle-check" :size="32" class="stat-icon" style="color: var(--mc-success)" />
          <div class="stat-info">
            <div class="stat-value">{{ stats.active_agents || 0 }}</div>
            <div class="stat-label">Working</div>
          </div>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
          <McIcon name="clock" :size="32" class="stat-icon" style="color: var(--mc-text-muted)" />
          <div class="stat-info">
            <div class="stat-value">{{ stats.idle_agents || 0 }}</div>
            <div class="stat-label">Idle</div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Office Floor -->
    <Panel header="Digital Office" class="office-panel">
      <div class="office-floor">
        <div
          v-for="station in workstations"
          :key="station.agent_id"
          class="workstation"
          :class="`workstation-${station.status}`"
          :style="getWorkstationStyle(station)"
        >
          <!-- Agent Avatar -->
          <div class="agent-avatar-large" :style="{ backgroundColor: station.avatar_color }">
            {{ getAgentInitials(station.display_name) }}
          </div>
          
          <!-- Workstation Name -->
          <div class="station-name">{{ station.display_name }}</div>
          
          <!-- Status Indicator -->
          <div class="status-indicator" :class="`status-${station.status}`">
            <McIcon :name="getStatusIcon(station.status)" :size="12" />
            {{ station.status }}
          </div>

          <!-- Computer Screen (shows current task) -->
          <div v-if="station.status === 'working'" class="computer-screen">
            <div class="screen-content">
              <McIcon name="zap" :size="24" class="screen-icon" />
              <div class="task-text">{{ station.current_task || 'Processing...' }}</div>
            </div>
          </div>
          <div v-else class="computer-screen screen-idle">
            <McIcon name="minus" :size="24" class="screen-icon" />
          </div>

          <!-- Last Seen -->
          <div v-if="station.last_seen" class="last-seen">
            Last active: {{ formatRelative(station.last_seen) }}
          </div>
        </div>
      </div>
    </Panel>

    <!-- Agent List -->
    <Panel header="Team Directory" class="directory-panel mt-4">
      <DataTable :value="workstations" :loading="loading" stripedRows size="small">
        <Column header="Agent">
          <template #body="slotProps">
            <div class="agent-cell">
              <span
                class="agent-avatar-small"
                :style="{ backgroundColor: slotProps.data.avatar_color }"
              >
                {{ getAgentInitials(slotProps.data.display_name) }}
              </span>
              {{ slotProps.data.display_name }}
            </div>
          </template>
        </Column>
        <Column field="status" header="Status">
          <template #body="slotProps">
            <Tag
              :value="slotProps.data.status"
              :severity="getStatusSeverity(slotProps.data.status)"
            >
              <McIcon :name="getStatusIcon(slotProps.data.status)" :size="12" />
              {{ slotProps.data.status }}
            </Tag>
          </template>
        </Column>
        <Column field="current_task" header="Current Task">
          <template #body="slotProps">
            <span v-if="slotProps.data.current_task" class="task-text-truncated">
              {{ slotProps.data.current_task }}
            </span>
            <span v-else class="text-muted">—</span>
          </template>
        </Column>
        <Column field="last_seen" header="Last Seen">
          <template #body="slotProps">
            <span v-if="slotProps.data.last_seen">
              {{ formatRelative(slotProps.data.last_seen) }}
            </span>
            <span v-else class="text-muted">Never</span>
          </template>
        </Column>
      </DataTable>
    </Panel>
  </div></PageShell>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useOfficeStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import Button from 'primevue/button'
import Panel from 'primevue/panel'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import type { components } from '@/types/api'

type AgentWorkstation = components['schemas']['AgentWorkstation']

const store = useOfficeStore()

const workstations = computed(() => store.workstations)
const stats = computed(() => store.stats)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

let refreshInterval: ReturnType<typeof setInterval>

onMounted(() => {
  store.fetchOffice()
  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(() => store.fetchOffice(), 30000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})

function refresh() {
  store.fetchOffice()
}

function getWorkstationStyle(station: AgentWorkstation) {
  return {
    left: `${station.position.x}px`,
    top: `${station.position.y}px`,
  }
}

function getAgentInitials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function getStatusIcon(status: string): string {
  const iconMap: Record<string, string> = {
    active: 'circle-check',
    working: 'zap',
    idle: 'clock',
    scheduled: 'calendar',
    offline: 'circle-x',
  }
  return iconMap[status] || 'minus'
}

function getStatusSeverity(status: string): string {
  const severityMap: Record<string, string> = {
    active: 'success',
    working: 'info',
    idle: 'secondary',
    scheduled: 'warning',
    offline: 'danger',
  }
  return severityMap[status] || 'secondary'
}

function formatRelative(dateStr: string | Date): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diffMs = now - then
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}
</script>

<style scoped>
.office-page {
  padding: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2rem;
  font-weight: 600;
  font-family: var(--mc-font-display);
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
}

.subtitle {
  color: var(--mc-text-muted);
  margin: 0;
}

.error-banner {
  background: color-mix(in srgb, var(--mc-danger) 15%, transparent);
  color: var(--mc-danger);
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

/* Stats */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card :deep(.p-card-content) {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}

.stat-icon {
  color: var(--mc-accent);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  margin-top: 0.25rem;
}

/* Office Floor */
.office-floor {
  position: relative;
  min-height: 700px;
  background: 
    linear-gradient(90deg, rgba(0,0,0,0.02) 1px, transparent 1px),
    linear-gradient(rgba(0,0,0,0.02) 1px, transparent 1px);
  background-size: 50px 50px;
  border-radius: 8px;
}

.workstation {
  position: absolute;
  width: 180px;
  padding: 1rem;
  background: var(--mc-bg-surface);
  border: 2px solid var(--mc-border);
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s;
}

.workstation:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: var(--mc-accent);
}

.workstation-working {
  border-color: var(--mc-info);
  box-shadow: 0 0 20px var(--mc-accent-glow);
}

.workstation-idle {
  opacity: 0.7;
}

.agent-avatar-large {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1.5rem;
  margin: 0 auto 0.75rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.station-name {
  font-weight: 600;
  font-family: var(--mc-font-display);
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.status-working {
  background: var(--mc-accent-subtle);
  color: var(--mc-info);
}

.status-idle {
  background: var(--mc-bg-hover);
  color: var(--mc-text-muted);
}

.status-active {
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
  color: var(--mc-success);
}

.computer-screen {
  background: var(--mc-bg-solid);
  border-radius: 4px;
  padding: 0.75rem;
  min-height: 80px;
  margin-bottom: 0.5rem;
  position: relative;
  overflow: hidden;
}

.screen-content {
  color: var(--mc-success);
  font-family: monospace;
  font-size: 0.7rem;
  line-height: 1.4;
}

.screen-icon {
  opacity: 0.3;
}

.screen-idle {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
}

.task-text {
  margin-top: 0.5rem;
  text-overflow: ellipsis;
  overflow: hidden;
  max-height: 3em;
}

.last-seen {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  font-style: italic;
}

/* Directory */
.agent-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.agent-avatar-small {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  color: white;
  font-weight: 600;
  font-size: 0.8rem;
}

.task-text-truncated {
  display: block;
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.85rem;
  font-family: monospace;
}

.text-muted {
  color: var(--mc-text-muted);
  font-style: italic;
}
</style>
