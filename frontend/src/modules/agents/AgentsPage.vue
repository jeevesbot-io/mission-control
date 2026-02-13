<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAgentsStore } from './store'
import { useWebSocket } from '@/composables/useWebSocket'
import PageShell from '@/components/layout/PageShell.vue'
import StatCard from '@/components/data/StatCard.vue'

const store = useAgentsStore()
const { subscribe } = useWebSocket()

onMounted(() => {
  store.fetchAgents()
  store.fetchStats()
  store.fetchCron()

  subscribe('agents:activity', (data) => {
    store.addActivity(data as { event: string; agent_id: string; message: string })
    // Refresh agents list on new activity
    store.fetchAgents()
    store.fetchStats()
  })
})

function statusClass(status: string | null): string {
  if (!status) return ''
  if (status === 'success') return 'agents__status--success'
  if (status === 'error' || status === 'failed') return 'agents__status--error'
  if (status === 'running' || status === 'pending') return 'agents__status--running'
  return ''
}

function formatDate(iso: string | null): string {
  if (!iso) return 'Never'
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function handleTrigger(agentId: string) {
  const ok = await store.triggerAgent(agentId)
  if (ok) {
    store.fetchAgents()
    store.fetchStats()
  }
}
</script>

<template>
  <PageShell>
    <div class="agents">
      <div class="agents__header">
        <h2 class="agents__title">Agent Control</h2>
        <p class="agents__subtitle">Monitor and trigger agent runs</p>
      </div>

      <!-- Stats -->
      <section class="agents__section" v-if="store.stats">
        <h3 class="agents__section-title">Telemetry</h3>
        <div class="agents__stats mc-stagger">
          <StatCard icon="&#x1f4ca;" :value="store.stats.total_runs" label="Total Runs" />
          <StatCard
            icon="&#x2705;"
            :value="`${store.stats.success_rate}%`"
            label="Success Rate"
          />
          <StatCard icon="&#x1f552;" :value="store.stats.runs_24h" label="Runs (24h)" />
          <StatCard icon="&#x1f916;" :value="store.stats.unique_agents" label="Unique Agents" />
        </div>
      </section>

      <!-- Agent Cards -->
      <section class="agents__section">
        <h3 class="agents__section-title">
          Agents
          <span class="agents__count">{{ store.agents.length }}</span>
        </h3>

        <div v-if="store.agents.length === 0 && !store.loading" class="agents__empty">
          <p>No agent runs recorded yet.</p>
        </div>

        <div class="agents__grid mc-stagger">
          <div
            v-for="agent in store.agents"
            :key="agent.agent_id"
            class="agents__card"
          >
            <div class="agents__card-header">
              <RouterLink
                :to="`/agents/${agent.agent_id}`"
                class="agents__card-name"
              >
                {{ agent.agent_id }}
              </RouterLink>
              <span class="agents__status" :class="statusClass(agent.last_status)">
                {{ agent.last_status ?? 'unknown' }}
              </span>
            </div>
            <div class="agents__card-meta">
              <span>{{ agent.total_runs }} runs</span>
              <span>Last: {{ formatDate(agent.last_run) }}</span>
            </div>
            <button class="agents__trigger-btn" @click="handleTrigger(agent.agent_id)">
              <i class="pi pi-play" /> Trigger
            </button>
          </div>
        </div>
      </section>

      <!-- Cron Schedule -->
      <section class="agents__section" v-if="store.cronJobs.length > 0">
        <h3 class="agents__section-title">Cron Schedule</h3>
        <div class="agents__cron-list">
          <div
            v-for="job in store.cronJobs"
            :key="job.agent_id"
            class="agents__cron-item"
          >
            <span class="agents__cron-agent mc-mono">{{ job.agent_id }}</span>
            <span class="agents__cron-schedule mc-mono">{{ job.schedule }}</span>
            <span
              class="agents__cron-status"
              :class="job.enabled ? 'agents__cron-status--on' : 'agents__cron-status--off'"
            >
              {{ job.enabled ? 'Active' : 'Disabled' }}
            </span>
          </div>
        </div>
      </section>

      <!-- Activity Feed -->
      <section class="agents__section" v-if="store.activityFeed.length > 0">
        <h3 class="agents__section-title">Live Activity</h3>
        <div class="agents__feed">
          <div
            v-for="(event, i) in store.activityFeed"
            :key="i"
            class="agents__feed-item"
          >
            <span class="agents__feed-time mc-mono">{{ formatDate(event.timestamp ?? null) }}</span>
            <span class="agents__feed-agent">{{ event.agent_id }}</span>
            <span class="agents__feed-msg">{{ event.message }}</span>
          </div>
        </div>
      </section>

      <!-- Error -->
      <div v-if="store.error" class="agents__error">
        <i class="pi pi-exclamation-triangle" />
        {{ store.error }}
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.agents {
  max-width: 1100px;
}

.agents__header {
  margin-bottom: 1.5rem;
}

.agents__title {
  font-family: var(--mc-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.agents__subtitle {
  color: var(--mc-text-muted);
  font-size: 0.9rem;
}

/* Sections */
.agents__section {
  margin-bottom: 2rem;
}

.agents__section-title {
  font-family: var(--mc-font-display);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mc-text-muted);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.agents__count {
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
  padding: 0.1rem 0.5rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-family: var(--mc-font-mono);
}

/* Stats */
.agents__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

/* Agent Cards */
.agents__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.agents__card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
  transition: border-color var(--mc-transition-speed), box-shadow var(--mc-transition-speed);
}

.agents__card:hover {
  border-color: var(--mc-border-strong);
  box-shadow: var(--mc-shadow-sm);
}

.agents__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.agents__card-name {
  font-family: var(--mc-font-display);
  font-weight: 600;
  font-size: 1rem;
  color: var(--mc-text);
  text-decoration: none;
}

.agents__card-name:hover {
  color: var(--mc-accent);
}

.agents__status {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
  background: var(--mc-bg-elevated);
}

.agents__status--success {
  color: var(--mc-success);
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
}

.agents__status--error {
  color: var(--mc-danger);
  background: color-mix(in srgb, var(--mc-danger) 10%, transparent);
}

.agents__status--running {
  color: var(--mc-live);
  background: color-mix(in srgb, var(--mc-live) 10%, transparent);
}

.agents__card-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.75rem;
}

.agents__trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.4rem 0.85rem;
  background: var(--mc-accent-subtle);
  border: 1px solid var(--mc-accent);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-accent);
  font-family: var(--mc-font-body);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: background var(--mc-transition-speed), color var(--mc-transition-speed);
}

.agents__trigger-btn:hover {
  background: var(--mc-accent);
  color: white;
}

/* Cron */
.agents__cron-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.agents__cron-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
}

.agents__cron-agent {
  font-weight: 500;
  min-width: 150px;
}

.agents__cron-schedule {
  color: var(--mc-text-muted);
  font-size: 0.8rem;
  flex: 1;
}

.agents__cron-status {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.1rem 0.5rem;
  border-radius: 99px;
}

.agents__cron-status--on {
  color: var(--mc-success);
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
}

.agents__cron-status--off {
  color: var(--mc-text-muted);
  background: var(--mc-bg-elevated);
}

/* Activity Feed */
.agents__feed {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  max-height: 300px;
  overflow-y: auto;
}

.agents__feed-item {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--mc-bg-surface);
  border-radius: var(--mc-radius-sm);
  font-size: 0.8rem;
}

.agents__feed-time {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

.agents__feed-agent {
  font-weight: 500;
  color: var(--mc-accent);
  flex-shrink: 0;
}

.agents__feed-msg {
  color: var(--mc-text-muted);
}

/* Empty / Error */
.agents__empty {
  text-align: center;
  padding: 2rem;
  color: var(--mc-text-muted);
}

.agents__error {
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
