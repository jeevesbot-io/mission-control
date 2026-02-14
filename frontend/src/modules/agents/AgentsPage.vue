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
    store.fetchAgents()
    store.fetchStats()
  })
})

function levelClass(level: string | null): string {
  if (!level) return ''
  if (level === 'info') return 'agents__level--info'
  if (level === 'warning') return 'agents__level--warning'
  if (level === 'error') return 'agents__level--error'
  return ''
}

function formatRelative(iso: string | null): string {
  if (!iso) return 'Never'
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
        <p class="agents__subtitle">Monitor agent activity and logs</p>
      </div>

      <!-- Stats -->
      <section class="agents__section" v-if="store.stats">
        <h3 class="agents__section-title">Telemetry</h3>
        <div class="agents__stats mc-stagger">
          <StatCard icon="📊" :value="store.stats.total_entries" label="Total Log Entries" />
          <StatCard
            icon="💚"
            :value="`${store.stats.health_rate}%`"
            label="Health Rate"
          />
          <StatCard icon="🕒" :value="store.stats.entries_24h" label="Entries (24h)" />
          <StatCard icon="🤖" :value="store.stats.unique_agents" label="Unique Agents" />
          <StatCard icon="⚠️" :value="store.stats.warning_count" label="Warnings" />
        </div>
      </section>

      <!-- Agent Cards -->
      <section class="agents__section">
        <h3 class="agents__section-title">
          Agents
          <span class="agents__count">{{ store.agents.length }}</span>
        </h3>

        <div v-if="store.agents.length === 0 && !store.loading" class="agents__empty">
          <p>No agent activity recorded yet.</p>
        </div>

        <div class="agents__grid mc-stagger">
          <div
            v-for="agent in store.agents"
            :key="agent.agent_id"
            class="agents__card"
          >
            <div class="agents__card-header">
              <div class="agents__card-name-row">
                <span class="agents__card-icon">{{ agentIcon(agent.agent_id) }}</span>
                <RouterLink
                  :to="`/agents/${agent.agent_id}`"
                  class="agents__card-name"
                >
                  {{ agent.agent_id }}
                </RouterLink>
              </div>
              <span class="agents__level" :class="levelClass(agent.last_level)">
                {{ agent.last_level ?? 'unknown' }}
              </span>
            </div>
            <div class="agents__card-message" v-if="agent.last_message">
              {{ agent.last_message }}
            </div>
            <div class="agents__card-meta">
              <span>{{ agent.total_entries }} entries</span>
              <span v-if="agent.warning_count > 0" class="agents__card-warnings">
                ⚠️ {{ agent.warning_count }} warnings
              </span>
              <span>Last: {{ formatRelative(agent.last_activity) }}</span>
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
            <span class="agents__feed-time mc-mono">{{ formatRelative(event.timestamp ?? null) }}</span>
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

.agents__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.agents__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
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

.agents__card-name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.agents__card-icon {
  font-size: 1.25rem;
}

.agents__card-name {
  font-family: var(--mc-font-display);
  font-weight: 600;
  font-size: 1rem;
  color: var(--mc-text);
  text-decoration: none;
  text-transform: capitalize;
}

.agents__card-name:hover {
  color: var(--mc-accent);
}

.agents__card-message {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agents__level {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
  background: var(--mc-bg-elevated);
}

.agents__level--info {
  color: var(--mc-success);
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
}

.agents__level--warning {
  color: var(--mc-warning);
  background: color-mix(in srgb, var(--mc-warning) 10%, transparent);
}

.agents__level--error {
  color: var(--mc-danger);
  background: color-mix(in srgb, var(--mc-danger) 10%, transparent);
}

.agents__card-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.75rem;
}

.agents__card-warnings {
  color: var(--mc-warning);
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
