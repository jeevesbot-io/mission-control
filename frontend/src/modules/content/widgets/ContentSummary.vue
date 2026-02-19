<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import McIcon from '@/components/ui/McIcon.vue'

interface PipelineStats {
  total: number
  by_stage: Record<string, number>
}

const api = useApi()
const stats = ref<PipelineStats | null>(null)
const error = ref(false)

onMounted(async () => {
  try {
    const data = await api.get<{ items: unknown[]; stats: PipelineStats }>('/api/content/')
    stats.value = data.stats
  } catch {
    error.value = true
  }
})

const activeCount = computed(() => {
  if (!stats.value?.by_stage) return 0
  const s = stats.value.by_stage
  return (s.scripting || 0) + (s.thumbnail || 0) + (s.filming || 0) + (s.editing || 0)
})
</script>

<template>
  <div class="content-summary">
    <div class="cs-header">
      <h3 class="cs-title">Content Pipeline</h3>
      <RouterLink to="/content" class="cs-link">View all</RouterLink>
    </div>

    <div v-if="error" class="cs-error">
      <McIcon name="alert-triangle" :size="14" />
      Content unavailable
    </div>

    <div v-else-if="!stats" class="cs-empty">Loading...</div>

    <div v-else class="cs-stats">
      <div class="stat-row">
        <McIcon name="file-text" :size="14" class="stat-icon" style="color: var(--mc-accent)" />
        <span class="stat-label">Total items</span>
        <span class="stat-value">{{ stats.total || 0 }}</span>
      </div>
      <div class="stat-row">
        <McIcon name="flame" :size="14" class="stat-icon" style="color: var(--mc-warning)" />
        <span class="stat-label">In progress</span>
        <span class="stat-value">{{ activeCount }}</span>
      </div>
      <div class="stat-row">
        <McIcon name="check-circle" :size="14" class="stat-icon" style="color: var(--mc-success)" />
        <span class="stat-label">Published</span>
        <span class="stat-value">{{ stats.by_stage?.published || 0 }}</span>
      </div>
      <div class="stat-row">
        <McIcon name="lightbulb" :size="14" class="stat-icon" style="color: #fbbf24" />
        <span class="stat-label">Ideas</span>
        <span class="stat-value">{{ stats.by_stage?.ideas || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content-summary {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
}

.cs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.cs-title {
  font-family: var(--mc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
}

.cs-link {
  font-size: 0.75rem;
  color: var(--mc-accent);
  text-decoration: none;
}
.cs-link:hover { color: var(--mc-accent-hover); }

.cs-stats { display: flex; flex-direction: column; gap: 0.5rem; }

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

.cs-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-warning);
  padding: 0.5rem;
}

.cs-empty {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  padding: 0.5rem;
}
</style>
