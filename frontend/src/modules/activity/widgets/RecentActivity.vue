<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import McIcon from '@/components/ui/McIcon.vue'

interface ActivityEvent {
  id: string
  timestamp: string
  actor: string
  action: string
  resource_type: string
  resource_name: string | null
  module: string
}

const api = useApi()
const events = ref<ActivityEvent[]>([])
const error = ref(false)

onMounted(async () => {
  try {
    const data = await api.get<{ events: ActivityEvent[] }>('/api/activity/feed?limit=5')
    events.value = data.events
  } catch {
    error.value = true
  }
})

function iconForResource(type: string): string {
  const map: Record<string, string> = {
    task: 'kanban',
    agent: 'bot',
    model: 'cpu',
    skill: 'sparkles',
    soul: 'file-text',
    content: 'video',
  }
  return map[type] || 'activity'
}

function actionLabel(action: string): string {
  const parts = action.split('.')
  if (parts.length === 2) return `${parts[0]} ${parts[1]}`
  return action.replace(/\./g, ' ')
}

function formatRelative(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = now - then
  const mins = Math.round(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}
</script>

<template>
  <div class="recent-activity">
    <div class="ra-header">
      <h3 class="ra-title">Recent Activity</h3>
      <RouterLink to="/activity" class="ra-link">View all</RouterLink>
    </div>

    <div v-if="error" class="ra-error">
      <McIcon name="alert-triangle" :size="14" />
      Activity unavailable
    </div>

    <div v-else-if="events.length === 0" class="ra-empty">No activity yet</div>

    <div v-else class="ra-list">
      <div
        v-for="event in events"
        :key="event.id"
        class="ra-item"
      >
        <McIcon :name="iconForResource(event.resource_type)" :size="14" class="ra-icon" />
        <div class="ra-content">
          <span class="ra-action">{{ actionLabel(event.action) }}</span>
          <span v-if="event.resource_name" class="ra-resource">{{ event.resource_name }}</span>
        </div>
        <span class="ra-time mc-mono">{{ formatRelative(event.timestamp) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recent-activity {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
}

.ra-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.ra-title {
  font-family: var(--mc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
}

.ra-link {
  font-size: 0.75rem;
  color: var(--mc-accent);
  text-decoration: none;
}
.ra-link:hover { color: var(--mc-accent-hover); }

.ra-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.ra-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.4rem;
  border-radius: var(--mc-radius-sm);
  transition: background var(--mc-transition-speed);
}

.ra-item:hover {
  background: var(--mc-bg-hover);
}

.ra-icon {
  flex-shrink: 0;
  color: var(--mc-text-muted);
}

.ra-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.ra-action {
  font-size: 0.78rem;
  font-weight: 500;
  text-transform: capitalize;
}

.ra-resource {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ra-time {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

.ra-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-warning);
  padding: 0.5rem;
}

.ra-empty {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  padding: 0.5rem;
}
</style>
