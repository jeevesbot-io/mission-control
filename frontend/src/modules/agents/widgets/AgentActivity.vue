<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useWebSocket } from '@/composables/useWebSocket'

interface AgentRun {
  id: string
  agent_id: string
  status: string
  created_at: string
  summary: string | null
}

const api = useApi()
const { subscribe } = useWebSocket()
const recentRuns = ref<AgentRun[]>([])
const error = ref(false)

onMounted(async () => {
  try {
    // Fetch most recent runs across all agents — use stats to find the most recent agent
    const agents = await api.get<{ agent_id: string }[]>('/api/agents/')
    const first = agents[0]
    if (first) {
      const data = await api.get<{ runs: AgentRun[] }>(
        `/api/agents/${first.agent_id}/runs?page_size=5`,
      )
      recentRuns.value = data.runs
    }
  } catch {
    error.value = true
  }

  subscribe('agents:activity', () => {
    // Refresh on new activity
    refreshRuns()
  })
})

async function refreshRuns() {
  try {
    const agents = await api.get<{ agent_id: string }[]>('/api/agents/')
    const first = agents[0]
    if (first) {
      const data = await api.get<{ runs: AgentRun[] }>(
        `/api/agents/${first.agent_id}/runs?page_size=5`,
      )
      recentRuns.value = data.runs
    }
  } catch {
    // Silent refresh failure
  }
}

function statusIcon(status: string): string {
  if (status === 'success') return '\u2705'
  if (status === 'error' || status === 'failed') return '\u274c'
  if (status === 'running') return '\u23f3'
  return '\u2796'
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="agent-activity">
    <div class="agent-activity__header">
      <h3 class="agent-activity__title">Agent Activity</h3>
      <RouterLink to="/agents" class="agent-activity__link">View all</RouterLink>
    </div>

    <div v-if="error" class="agent-activity__error">
      <i class="pi pi-exclamation-triangle" />
      Agents module unavailable
    </div>

    <div v-else-if="recentRuns.length === 0" class="agent-activity__empty">
      No recent agent activity
    </div>

    <div v-else class="agent-activity__list">
      <div
        v-for="run in recentRuns"
        :key="run.id"
        class="agent-activity__item"
      >
        <span class="agent-activity__icon">{{ statusIcon(run.status) }}</span>
        <div class="agent-activity__info">
          <span class="agent-activity__agent">{{ run.agent_id }}</span>
          <span class="agent-activity__summary">{{ run.summary ?? run.status }}</span>
        </div>
        <span class="agent-activity__time mc-mono">{{ formatTime(run.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-activity {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
}

.agent-activity__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.agent-activity__title {
  font-family: var(--mc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
}

.agent-activity__link {
  font-size: 0.75rem;
  color: var(--mc-accent);
  text-decoration: none;
}

.agent-activity__link:hover {
  color: var(--mc-accent-hover);
}

.agent-activity__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.agent-activity__item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.6rem;
  border-radius: var(--mc-radius-sm);
  transition: background var(--mc-transition-speed);
}

.agent-activity__item:hover {
  background: var(--mc-bg-hover);
}

.agent-activity__icon {
  font-size: 0.85rem;
  flex-shrink: 0;
}

.agent-activity__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.agent-activity__agent {
  font-size: 0.8rem;
  font-weight: 500;
}

.agent-activity__summary {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-activity__time {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

.agent-activity__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-warning);
  padding: 0.5rem;
}

.agent-activity__empty {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  padding: 0.5rem;
}
</style>
