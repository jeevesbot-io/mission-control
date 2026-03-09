<script setup lang="ts">
import { computed } from 'vue'
import McIcon from '@/components/ui/McIcon.vue'
import McChip from '@/components/ui/McChip.vue'
import McLoadingState from '@/components/ui/McLoadingState.vue'
import McEmptyState from '@/components/ui/McEmptyState.vue'
import { useHeatmapStore } from '../store'

const store = useHeatmapStore()

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const mins = Math.floor(ms / 60000)
  const secs = Math.round((ms % 60000) / 1000)
  return `${mins}m ${secs}s`
}

function formatDisplayDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}

const outcomeColor = (outcome: string): string => {
  switch (outcome) {
    case 'success': return 'green'
    case 'error':
    case 'failure': return 'red'
    case 'timeout': return 'orange'
    default: return 'amber'
  }
}
</script>

<template>
  <div class="day-detail">
    <div class="day-detail__header">
      <div class="day-detail__title-row">
        <h3 class="day-detail__title">
          {{ store.selectedDate ? formatDisplayDate(store.selectedDate) : '' }}
        </h3>
        <span class="day-detail__count mc-mono">
          {{ store.filteredDayRuns.length }} run{{ store.filteredDayRuns.length === 1 ? '' : 's' }}
        </span>
      </div>
      <button class="day-detail__close" @click="store.selectDate(null)" title="Close">
        <McIcon name="x" :size="16" />
      </button>
    </div>

    <McLoadingState v-if="store.dayLoading" label="Loading runs…" />

    <McEmptyState
      v-else-if="store.filteredDayRuns.length === 0"
      icon="flame"
      title="No runs"
      description="No agent runs recorded for this day."
    />

    <div v-else class="day-detail__runs">
      <div
        v-for="run in store.filteredDayRuns"
        :key="run.id"
        class="day-detail__run"
      >
        <div class="day-detail__run-header">
          <McChip :color="outcomeColor(run.outcome)" size="sm" mono uppercase>
            {{ run.outcome }}
          </McChip>
          <span class="day-detail__run-agent mc-mono">{{ run.agent_id }}</span>
          <span class="day-detail__run-time mc-mono">{{ formatTime(run.created_at) }}</span>
        </div>

        <div class="day-detail__run-meta">
          <span v-if="run.trigger" class="day-detail__meta-item">
            <span class="day-detail__meta-label">trigger</span>
            <span class="day-detail__meta-value">{{ run.trigger }}</span>
          </span>
          <span v-if="run.channel" class="day-detail__meta-item">
            <span class="day-detail__meta-label">channel</span>
            <span class="day-detail__meta-value">{{ run.channel }}</span>
          </span>
          <span class="day-detail__meta-item">
            <span class="day-detail__meta-label">duration</span>
            <span class="day-detail__meta-value">{{ formatDuration(run.duration_ms) }}</span>
          </span>
        </div>

        <div v-if="run.prompt_preview" class="day-detail__prompt">
          {{ run.prompt_preview }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.day-detail {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  margin-top: var(--mc-space-4);
  animation: mc-fade-up 0.25s ease-out;
}

.day-detail__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--mc-space-3) var(--mc-space-4);
  border-bottom: 1px solid var(--mc-border);
}

.day-detail__title-row {
  display: flex;
  align-items: center;
  gap: var(--mc-space-2);
}

.day-detail__title {
  font-family: var(--mc-font-display);
  font-size: var(--mc-text-sm);
  font-weight: 600;
  color: var(--mc-text);
  margin: 0;
}

.day-detail__count {
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
}

.day-detail__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--mc-radius-xs);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-fast);
}

.day-detail__close:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
  border-color: var(--mc-border);
}

/* Runs list */
.day-detail__runs {
  max-height: 400px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--mc-border-strong) transparent;
}

.day-detail__run {
  padding: var(--mc-space-3) var(--mc-space-4);
  border-bottom: 1px solid var(--mc-border);
  transition: background var(--mc-transition-fast);
}

.day-detail__run:last-child {
  border-bottom: none;
}

.day-detail__run:hover {
  background: var(--mc-bg-hover);
}

.day-detail__run-header {
  display: flex;
  align-items: center;
  gap: var(--mc-space-2);
  margin-bottom: var(--mc-space-1);
}

.day-detail__run-agent {
  font-size: var(--mc-text-xs);
  color: var(--mc-color-amber);
  font-weight: 500;
}

.day-detail__run-time {
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
  margin-left: auto;
}

.day-detail__run-meta {
  display: flex;
  align-items: center;
  gap: var(--mc-space-4);
  margin-top: var(--mc-space-1);
}

.day-detail__meta-item {
  display: flex;
  align-items: center;
  gap: var(--mc-space-1);
}

.day-detail__meta-label {
  font-size: 9px;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.day-detail__meta-value {
  font-size: var(--mc-text-xs);
  font-family: var(--mc-font-mono);
  color: var(--mc-text);
}

.day-detail__prompt {
  margin-top: var(--mc-space-2);
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.mc-mono {
  font-family: var(--mc-font-mono);
}
</style>
