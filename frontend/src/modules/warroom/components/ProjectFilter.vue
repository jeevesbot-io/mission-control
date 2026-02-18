<template>
  <div class="project-filter">
    <button
      class="filter-btn"
      :class="{ active: store.filterProject === null }"
      @click="store.setProjectFilter(null)"
    >
      All
    </button>
    <button
      v-for="project in store.activeProjectsWithCounts"
      :key="project.id"
      class="filter-btn"
      :class="{ active: store.filterProject === project.id }"
      :style="activeStyle(project)"
      @click="store.setProjectFilter(project.id)"
    >
      {{ project.name }}
      <span class="count">{{ project.task_count }}</span>
    </button>
    <button
      class="filter-btn untagged"
      :class="{ active: store.filterProject === 'untagged' }"
      @click="store.setProjectFilter('untagged')"
    >
      Unassigned
    </button>
  </div>
</template>

<script setup lang="ts">
import { useWarRoomStore } from '../store'

const store = useWarRoomStore()

const COLOR_TEXT: Record<string, string> = {
  purple: '#a78bfa', pink: '#f472b6', green: '#34d399', blue: '#60a5fa',
  amber: '#fbbf24', indigo: '#818cf8', red: '#f87171', orange: '#fb923c',
  cyan: '#22d3ee', yellow: '#fde047',
}

function activeStyle(project: { color: string; id: string }) {
  if (store.filterProject !== project.id) return {}
  const color = COLOR_TEXT[project.color] ?? 'var(--mc-accent)'
  return { color, borderColor: color, backgroundColor: `${color}15` }
}
</script>

<style scoped>
.project-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-family: var(--mc-font-mono);
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.04);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
  white-space: nowrap;
}
.filter-btn:hover {
  background: rgba(255,255,255,0.08);
  color: var(--mc-text);
}
.filter-btn.active {
  border-color: var(--mc-accent);
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
}
.filter-btn.untagged.active {
  border-color: rgba(107,112,132,0.5);
  background: rgba(107,112,132,0.12);
  color: var(--mc-text-muted);
}

.count {
  background: rgba(255,255,255,0.1);
  padding: 0 4px;
  border-radius: 8px;
  font-size: 0.65rem;
}
</style>
