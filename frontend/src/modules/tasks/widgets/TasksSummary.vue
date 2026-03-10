<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import McIcon from '@/components/ui/McIcon.vue'

interface TasksStats {
  in_progress_count: number
  todo_count: number
  last_heartbeat: number | null
  active_model: string
}

const api = useApi()
const stats = ref<TasksStats | null>(null)
const error = ref(false)

const totalActive = computed(() =>
  stats.value ? stats.value.in_progress_count + stats.value.todo_count : 0,
)

onMounted(async () => {
  try {
    stats.value = await api.get<TasksStats>('/api/warroom/stats')
  } catch {
    error.value = true
  }
})
</script>

<template>
  <div class="tasks-summary">
    <div class="ts-header">
      <h3 class="ts-title">Tasks</h3>
      <RouterLink to="/tasks" class="ts-link">View all</RouterLink>
    </div>

    <div v-if="error" class="ts-error">
      <McIcon name="alert-triangle" :size="14" />
      Tasks unavailable
    </div>

    <div v-else-if="!stats" class="ts-empty">Loading…</div>

    <div v-else class="ts-stats">
      <div class="stat-row">
        <McIcon name="flame" :size="14" class="stat-icon" style="color: var(--mc-warning)" />
        <span class="stat-label">In progress</span>
        <span class="stat-value">{{ stats.in_progress_count }}</span>
      </div>
      <div class="stat-row">
        <McIcon name="circle-dot" :size="14" class="stat-icon" style="color: var(--mc-info)" />
        <span class="stat-label">Todo</span>
        <span class="stat-value">{{ stats.todo_count }}</span>
      </div>
      <div class="stat-row">
        <McIcon name="check-square" :size="14" class="stat-icon" style="color: var(--mc-text-muted)" />
        <span class="stat-label">Total active</span>
        <span class="stat-value">{{ totalActive }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tasks-summary {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
}

.ts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.ts-title {
  font-family: var(--mc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
}

.ts-link {
  font-size: 0.75rem;
  color: var(--mc-accent);
  text-decoration: none;
}
.ts-link:hover { color: var(--mc-accent-hover); }

.ts-stats { display: flex; flex-direction: column; gap: 0.5rem; }

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

.ts-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-warning);
  padding: 0.5rem;
}

.ts-empty {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  padding: 0.5rem;
}
</style>
