<script setup lang="ts">
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import McLoadingState from '@/components/ui/McLoadingState.vue'
import McEmptyState from '@/components/ui/McEmptyState.vue'
import HeatmapGrid from './components/HeatmapGrid.vue'
import DayDetail from './components/DayDetail.vue'
import { useHeatmapStore } from './store'
import { computed, onMounted } from 'vue'

const store = useHeatmapStore()

onMounted(() => {
  if (!store.heatmapData.length && !store.loading) {
    store.fetchHeatmap()
  }
})

const totalRuns = computed(() =>
  store.heatmapData.reduce((sum, d) => sum + d.count, 0),
)

const activeDays = computed(() =>
  store.heatmapData.filter((d) => d.count > 0).length,
)

const topAgent = computed(() => {
  const counts: Record<string, number> = {}
  for (const day of store.heatmapData) {
    for (const a of day.agents) {
      counts[a.agent_id] = (counts[a.agent_id] || 0) + a.count
    }
  }
  let best = ''
  let max = 0
  for (const [id, c] of Object.entries(counts)) {
    if (c > max) { best = id; max = c }
  }
  return best ? { id: best, count: max } : null
})
</script>

<template>
  <PageShell>
    <div class="heatmap-page">
      <!-- Page header -->
      <div class="heatmap-page__header">
        <div class="heatmap-page__title-row">
          <McIcon name="flame" :size="22" />
          <h1 class="heatmap-page__title">Activity</h1>
        </div>
      </div>

      <!-- Stats bar -->
      <div v-if="!store.loading && store.heatmapData.length > 0" class="heatmap-page__stats">
        <div class="heatmap-page__stat">
          <span class="heatmap-page__stat-value mc-mono">{{ totalRuns.toLocaleString() }}</span>
          <span class="heatmap-page__stat-label">total runs</span>
        </div>
        <div class="heatmap-page__stat">
          <span class="heatmap-page__stat-value mc-mono">{{ activeDays }}</span>
          <span class="heatmap-page__stat-label">active days</span>
        </div>
        <div v-if="topAgent" class="heatmap-page__stat">
          <span class="heatmap-page__stat-value mc-mono">{{ topAgent.id }}</span>
          <span class="heatmap-page__stat-label">top agent ({{ topAgent.count }})</span>
        </div>
        <div class="heatmap-page__stat">
          <span class="heatmap-page__stat-value mc-mono">{{ store.agents.length }}</span>
          <span class="heatmap-page__stat-label">agents</span>
        </div>
      </div>

      <!-- Loading / Empty / Grid -->
      <McLoadingState v-if="store.loading" label="Loading activity data…" />

      <template v-else-if="store.error">
        <McEmptyState
          icon="alert-triangle"
          :title="store.error"
          description="Failed to load heatmap data. Check that the API is running."
        />
      </template>

      <template v-else>
        <div class="heatmap-page__grid-card">
          <HeatmapGrid />
        </div>

        <!-- Day detail panel -->
        <DayDetail v-if="store.selectedDate" />
      </template>
    </div>
  </PageShell>
</template>

<style scoped>
.heatmap-page {
  max-width: 1100px;
}

/* Header */
.heatmap-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--mc-space-4);
}

.heatmap-page__title-row {
  display: flex;
  align-items: center;
  gap: var(--mc-space-2);
  color: var(--mc-color-amber);
}

.heatmap-page__title {
  font-family: var(--mc-font-display);
  font-size: var(--mc-text-2xl);
  font-weight: 700;
  color: var(--mc-text);
  margin: 0;
}

/* Stats */
.heatmap-page__stats {
  display: flex;
  gap: var(--mc-space-6);
  margin-bottom: var(--mc-space-5);
  padding: var(--mc-space-3) 0;
  border-bottom: 1px solid var(--mc-border);
}

.heatmap-page__stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.heatmap-page__stat-value {
  font-size: var(--mc-text-base);
  font-weight: 600;
  color: var(--mc-text);
}

.heatmap-page__stat-label {
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Grid card */
.heatmap-page__grid-card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: var(--mc-space-4);
}

.mc-mono {
  font-family: var(--mc-font-mono);
}
</style>
