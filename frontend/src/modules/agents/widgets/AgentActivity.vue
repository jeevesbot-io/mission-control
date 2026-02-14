<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useWebSocket } from '@/composables/useWebSocket'
import McIcon from '@/components/ui/McIcon.vue'
import { getLevelIconName } from '@/composables/useIcons'

interface AgentLogEntry {
  id: number
  agent_id: string
  level: string
  message: string
  created_at: string
}

interface AgentInfo {
  agent_id: string
}

const api = useApi()
const { subscribe } = useWebSocket()
const recentEntries = ref<AgentLogEntry[]>([])
const error = ref(false)

onMounted(async () => {
  await refreshLog()
  subscribe('agents:activity', () => refreshLog())
})

async function refreshLog() {
  try {
    const agents = await api.get<AgentInfo[]>('/api/agents/')
    const first = agents[0]
    if (first) {
      const data = await api.get<{ entries: AgentLogEntry[] }>(
        `/api/agents/${first.agent_id}/log?page_size=5`,
      )
      recentEntries.value = data.entries
    }
  } catch {
    error.value = true
  }
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

    <div v-else-if="recentEntries.length === 0" class="agent-activity__empty">
      No recent agent activity
    </div>

    <div v-else class="agent-activity__list">
      <div
        v-for="entry in recentEntries"
        :key="entry.id"
        class="agent-activity__item"
      >
        <McIcon :name="getLevelIconName(entry.level)" :size="16" class="agent-activity__icon" />
        <div class="agent-activity__info">
          <span class="agent-activity__agent">{{ entry.agent_id }}</span>
          <span class="agent-activity__summary">{{ entry.message }}</span>
        </div>
        <span class="agent-activity__time mc-mono">{{ formatTime(entry.created_at) }}</span>
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
  text-transform: capitalize;
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
