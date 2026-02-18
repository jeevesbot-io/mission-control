<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import McIcon from '@/components/ui/McIcon.vue'

interface WarRoomStats {
  in_progress_count: number
  todo_count: number
  last_heartbeat: number | null
  active_model: string
}

const api = useApi()
const stats = ref<WarRoomStats | null>(null)
const error = ref(false)

onMounted(async () => {
  try {
    stats.value = await api.get<WarRoomStats>('/api/warroom/stats')
  } catch {
    error.value = true
  }
})

function heartbeatAge(last: number | null): string {
  if (!last) return 'never'
  const ms = Date.now() - last
  const min = Math.floor(ms / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const h = Math.floor(min / 60)
  return `${h}h ago`
}

function heartbeatColor(last: number | null): string {
  if (!last) return 'var(--mc-text-muted)'
  const ms = Date.now() - last
  if (ms < 10 * 60_000) return 'var(--mc-success)'
  if (ms < 60 * 60_000) return 'var(--mc-warning)'
  return 'var(--mc-danger)'
}
</script>

<template>
  <div class="warroom-summary">
    <div class="ws-header">
      <h3 class="ws-title">War Room</h3>
      <RouterLink to="/warroom" class="ws-link">View all</RouterLink>
    </div>

    <div v-if="error" class="ws-error">
      <McIcon name="alert-triangle" :size="14" />
      War Room unavailable
    </div>

    <div v-else-if="!stats" class="ws-empty">Loading…</div>

    <div v-else class="ws-stats">
      <div class="stat-row">
        <McIcon name="flame" :size="14" class="stat-icon" style="color: var(--mc-warning)" />
        <span class="stat-label">In progress</span>
        <span class="stat-value">{{ stats.in_progress_count }}</span>
      </div>
      <div class="stat-row">
        <McIcon name="kanban" :size="14" class="stat-icon" style="color: var(--mc-accent)" />
        <span class="stat-label">In queue</span>
        <span class="stat-value">{{ stats.todo_count }}</span>
      </div>
      <div class="stat-row">
        <span class="hb-dot" :style="{ background: heartbeatColor(stats.last_heartbeat) }" />
        <span class="stat-label">Last heartbeat</span>
        <span class="stat-value mc-mono">{{ heartbeatAge(stats.last_heartbeat) }}</span>
      </div>
      <div class="stat-row">
        <McIcon name="cpu" :size="14" class="stat-icon" style="color: var(--mc-text-muted)" />
        <span class="stat-label">Model</span>
        <span class="stat-value mc-mono">{{ stats.active_model.replace('anthropic/', '') }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.warroom-summary {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
}

.ws-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.ws-title {
  font-family: var(--mc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
}

.ws-link {
  font-size: 0.75rem;
  color: var(--mc-accent);
  text-decoration: none;
}
.ws-link:hover { color: var(--mc-accent-hover); }

.ws-stats { display: flex; flex-direction: column; gap: 0.5rem; }

.stat-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.4rem;
  border-radius: var(--mc-radius-sm);
  transition: background var(--mc-transition-speed);
}
.stat-row:hover { background: var(--mc-bg-hover); }

.stat-icon { flex-shrink: 0; }

.hb-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-label {
  flex: 1;
  font-size: 0.78rem;
  color: var(--mc-text-muted);
}

.stat-value {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--mc-text);
}

.ws-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-warning);
  padding: 0.5rem;
}

.ws-empty {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  padding: 0.5rem;
}
</style>
