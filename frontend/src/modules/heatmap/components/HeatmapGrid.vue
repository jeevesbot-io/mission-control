<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import McIcon from '@/components/ui/McIcon.vue'
import { useHeatmapStore, type HeatmapDay } from '../store'

const store = useHeatmapStore()

// ---------------------------------------------------------------------------
// Tooltip state
// ---------------------------------------------------------------------------
const tooltip = ref<{
  visible: boolean
  x: number
  y: number
  day: HeatmapDay | null
  date: string
}>({ visible: false, x: 0, y: 0, day: null, date: '' })

// ---------------------------------------------------------------------------
// Grid computation
// ---------------------------------------------------------------------------

const DAY_LABELS = ['Mon', '', 'Wed', '', 'Fri', '', 'Sun']
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** Generate the grid of weeks for the current year */
const weeks = computed(() => {
  const y = store.year
  // Start from the first Monday on or before Jan 1
  const jan1 = new Date(y, 0, 1)
  const startDay = jan1.getDay() // 0=Sun
  // Adjust to Monday-based: Mon=0, Tue=1 ... Sun=6
  const mondayOffset = startDay === 0 ? 6 : startDay - 1
  const gridStart = new Date(y, 0, 1 - mondayOffset)

  const result: { date: string; inYear: boolean }[][] = []
  const current = new Date(gridStart)
  const endDate = new Date(y, 11, 31)

  // Always produce 53 weeks max to cover the full year
  for (let w = 0; w < 53; w++) {
    const week: { date: string; inYear: boolean }[] = []
    for (let d = 0; d < 7; d++) {
      const dateStr = formatDate(current)
      const inYear = current.getFullYear() === y
      week.push({ date: dateStr, inYear })
      current.setDate(current.getDate() + 1)
    }
    result.push(week)
    // Stop if we've passed the year
    if (current > endDate && current.getFullYear() > y) break
  }
  return result
})

/** Month label positions along the top */
const monthLabels = computed(() => {
  const labels: { month: string; col: number }[] = []
  let lastMonth = -1
  for (let w = 0; w < weeks.value.length; w++) {
    // Use the Monday of each week to determine the month
    const monday = weeks.value[w][0]
    if (!monday.inYear) continue
    const month = parseInt(monday.date.substring(5, 7), 10) - 1
    if (month !== lastMonth) {
      labels.push({ month: MONTH_NAMES[month], col: w })
      lastMonth = month
    }
  }
  return labels
})

/** Get the count for a given date, respecting agent filter */
function getCount(date: string): number {
  const day = store.heatmapMap.get(date)
  if (!day) return 0
  if (!store.agentFilter) return day.count
  const agent = day.agents.find((a) => a.agent_id === store.agentFilter)
  return agent?.count ?? 0
}

/** Compute the max count for scaling */
const maxCount = computed(() => {
  let max = 0
  for (const day of store.heatmapData) {
    const c = store.agentFilter
      ? (day.agents.find((a) => a.agent_id === store.agentFilter)?.count ?? 0)
      : day.count
    if (c > max) max = c
  }
  return max
})

/** Get intensity level 0–4 */
function getLevel(date: string): number {
  const count = getCount(date)
  if (count === 0) return 0
  if (maxCount.value === 0) return 0
  const ratio = count / maxCount.value
  if (ratio <= 0.25) return 1
  if (ratio <= 0.5) return 2
  if (ratio <= 0.75) return 3
  return 4
}

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatDisplayDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
}

// ---------------------------------------------------------------------------
// Interactions
// ---------------------------------------------------------------------------

function onCellHover(event: MouseEvent, date: string, inYear: boolean) {
  if (!inYear) return
  const day = store.heatmapMap.get(date) ?? null
  const rect = (event.target as HTMLElement).getBoundingClientRect()
  tooltip.value = {
    visible: true,
    x: rect.left + rect.width / 2,
    y: rect.top - 8,
    day,
    date,
  }
}

function onCellLeave() {
  tooltip.value.visible = false
}

function onCellClick(date: string, inYear: boolean) {
  if (!inYear) return
  if (store.selectedDate === date) {
    store.selectDate(null)
  } else {
    store.selectDate(date)
  }
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => {
  store.fetchHeatmap()
})

watch(() => store.year, () => {
  store.fetchHeatmap()
})
</script>

<template>
  <div class="heatmap-grid">
    <!-- Year navigation -->
    <div class="heatmap-grid__header">
      <div class="heatmap-grid__year-nav">
        <button class="heatmap-grid__nav-btn" @click="store.setYear(store.year - 1)" title="Previous year">
          <McIcon name="chevron-left" :size="16" />
        </button>
        <span class="heatmap-grid__year">{{ store.year }}</span>
        <button class="heatmap-grid__nav-btn" @click="store.setYear(store.year + 1)" title="Next year">
          <McIcon name="chevron-right" :size="16" />
        </button>
      </div>

      <!-- Agent filter -->
      <div class="heatmap-grid__filter">
        <select
          class="heatmap-grid__select"
          :value="store.agentFilter ?? ''"
          @change="store.setAgentFilter(($event.target as HTMLSelectElement).value || null)"
        >
          <option value="">All agents</option>
          <option v-for="agent in store.agents" :key="agent" :value="agent">{{ agent }}</option>
        </select>
      </div>
    </div>

    <!-- Grid -->
    <div class="heatmap-grid__container">
      <!-- Day labels (left) -->
      <div class="heatmap-grid__day-labels">
        <div class="heatmap-grid__month-spacer"></div>
        <div v-for="(label, i) in DAY_LABELS" :key="i" class="heatmap-grid__day-label">
          {{ label }}
        </div>
      </div>

      <div class="heatmap-grid__scroll">
        <!-- Month labels (top) -->
        <div class="heatmap-grid__month-labels" :style="{ width: `${weeks.length * 15}px` }">
          <span
            v-for="ml in monthLabels"
            :key="ml.month + ml.col"
            class="heatmap-grid__month-label"
            :style="{ left: `${ml.col * 15}px` }"
          >
            {{ ml.month }}
          </span>
        </div>

        <!-- Cells -->
        <div class="heatmap-grid__cells">
          <div v-for="(week, wi) in weeks" :key="wi" class="heatmap-grid__week">
            <div
              v-for="(day, di) in week"
              :key="day.date"
              class="heatmap-grid__cell"
              :class="[
                `heatmap-grid__cell--level-${day.inYear ? getLevel(day.date) : 'empty'}`,
                { 'heatmap-grid__cell--outside': !day.inYear },
                { 'heatmap-grid__cell--selected': store.selectedDate === day.date },
              ]"
              @mouseenter="onCellHover($event, day.date, day.inYear)"
              @mouseleave="onCellLeave"
              @click="onCellClick(day.date, day.inYear)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="heatmap-grid__legend">
      <span class="heatmap-grid__legend-label">Less</span>
      <div class="heatmap-grid__cell heatmap-grid__cell--level-0 heatmap-grid__legend-cell" />
      <div class="heatmap-grid__cell heatmap-grid__cell--level-1 heatmap-grid__legend-cell" />
      <div class="heatmap-grid__cell heatmap-grid__cell--level-2 heatmap-grid__legend-cell" />
      <div class="heatmap-grid__cell heatmap-grid__cell--level-3 heatmap-grid__legend-cell" />
      <div class="heatmap-grid__cell heatmap-grid__cell--level-4 heatmap-grid__legend-cell" />
      <span class="heatmap-grid__legend-label">More</span>
    </div>

    <!-- Tooltip -->
    <Teleport to="body">
      <Transition name="tooltip">
        <div
          v-if="tooltip.visible"
          class="heatmap-tooltip"
          :style="{
            position: 'fixed',
            left: `${tooltip.x}px`,
            top: `${tooltip.y}px`,
            transform: 'translate(-50%, -100%)',
            pointerEvents: 'none',
          }"
          ref="tooltipEl"
        >
          <div class="heatmap-tooltip__date">{{ formatDisplayDate(tooltip.date) }}</div>
          <div class="heatmap-tooltip__count">
            {{ tooltip.day ? tooltip.day.count : 0 }} run{{ (tooltip.day?.count ?? 0) === 1 ? '' : 's' }}
          </div>
          <div v-if="tooltip.day && tooltip.day.agents.length > 0" class="heatmap-tooltip__agents">
            <div
              v-for="agent in tooltip.day.agents.slice(0, 3)"
              :key="agent.agent_id"
              class="heatmap-tooltip__agent"
            >
              <span class="heatmap-tooltip__agent-name">{{ agent.agent_id }}</span>
              <span class="heatmap-tooltip__agent-count">{{ agent.count }}</span>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.heatmap-grid {
  position: relative;
}

/* Header */
.heatmap-grid__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--mc-space-4);
}

.heatmap-grid__year-nav {
  display: flex;
  align-items: center;
  gap: var(--mc-space-2);
}

.heatmap-grid__nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-xs);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-fast);
}

.heatmap-grid__nav-btn:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
  border-color: var(--mc-border-strong);
}

.heatmap-grid__year {
  font-family: var(--mc-font-mono);
  font-size: var(--mc-text-lg);
  font-weight: 600;
  color: var(--mc-text);
  min-width: 60px;
  text-align: center;
}

.heatmap-grid__filter {
  display: flex;
  align-items: center;
}

.heatmap-grid__select {
  height: 30px;
  padding: 0 var(--mc-space-3);
  padding-right: var(--mc-space-6);
  font-family: var(--mc-font-body);
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
  background: transparent;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-full);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7084' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  transition: all var(--mc-transition-fast);
}

.heatmap-grid__select:hover {
  color: var(--mc-text);
  border-color: var(--mc-border-strong);
}

.heatmap-grid__select:focus {
  outline: none;
  border-color: var(--mc-accent);
}

/* Grid container */
.heatmap-grid__container {
  display: flex;
  gap: var(--mc-space-1);
}

.heatmap-grid__day-labels {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
  padding-right: var(--mc-space-1);
}

.heatmap-grid__month-spacer {
  height: 18px;
}

.heatmap-grid__day-label {
  height: 11px;
  font-size: 9px;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  display: flex;
  align-items: center;
  line-height: 1;
}

.heatmap-grid__scroll {
  overflow-x: auto;
  scrollbar-width: none;
  flex: 1;
}

.heatmap-grid__scroll::-webkit-scrollbar {
  display: none;
}

/* Month labels */
.heatmap-grid__month-labels {
  position: relative;
  height: 18px;
  margin-bottom: 2px;
}

.heatmap-grid__month-label {
  position: absolute;
  font-size: 9px;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  top: 0;
  white-space: nowrap;
}

/* Cells */
.heatmap-grid__cells {
  display: flex;
  gap: 2px;
}

.heatmap-grid__week {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.heatmap-grid__cell {
  width: 11px;
  height: 11px;
  border-radius: 2px;
  cursor: pointer;
  transition: all var(--mc-transition-fast);
}

.heatmap-grid__cell--outside {
  visibility: hidden;
}

.heatmap-grid__cell--level-empty {
  visibility: hidden;
}

.heatmap-grid__cell--level-0 {
  background: var(--mc-bg-hover);
}

.heatmap-grid__cell--level-1 {
  background: rgba(251, 191, 36, 0.2);
}

.heatmap-grid__cell--level-2 {
  background: rgba(251, 191, 36, 0.4);
}

.heatmap-grid__cell--level-3 {
  background: rgba(251, 191, 36, 0.65);
}

.heatmap-grid__cell--level-4 {
  background: rgba(251, 191, 36, 0.9);
}

.heatmap-grid__cell:hover:not(.heatmap-grid__cell--outside) {
  outline: 1px solid var(--mc-text-muted);
  outline-offset: -1px;
}

.heatmap-grid__cell--selected {
  outline: 2px solid var(--mc-color-amber) !important;
  outline-offset: -1px;
}

/* Legend */
.heatmap-grid__legend {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-top: var(--mc-space-3);
  justify-content: flex-end;
}

.heatmap-grid__legend-label {
  font-size: 9px;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
  margin: 0 var(--mc-space-1);
}

.heatmap-grid__legend-cell {
  cursor: default;
}

.heatmap-grid__legend-cell:hover {
  outline: none;
}

/* Tooltip */
.heatmap-tooltip {
  z-index: 9999;
  background: var(--mc-bg-elevated);
  border: 1px solid var(--mc-border-strong);
  border-radius: var(--mc-radius-sm);
  padding: var(--mc-space-2) var(--mc-space-3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  min-width: 140px;
}

.heatmap-tooltip__date {
  font-size: var(--mc-text-xs);
  font-weight: 600;
  color: var(--mc-text);
  margin-bottom: 2px;
}

.heatmap-tooltip__count {
  font-size: var(--mc-text-xs);
  font-family: var(--mc-font-mono);
  color: var(--mc-color-amber);
  margin-bottom: 4px;
}

.heatmap-tooltip__agents {
  display: flex;
  flex-direction: column;
  gap: 1px;
  border-top: 1px solid var(--mc-border);
  padding-top: 4px;
}

.heatmap-tooltip__agent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--mc-space-3);
}

.heatmap-tooltip__agent-name {
  font-size: 9px;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
}

.heatmap-tooltip__agent-count {
  font-size: 9px;
  font-family: var(--mc-font-mono);
  color: var(--mc-text);
}

/* Tooltip transition */
.tooltip-enter-active { transition: opacity 0.1s ease; }
.tooltip-leave-active { transition: opacity 0.08s ease; }
.tooltip-enter-from,
.tooltip-leave-to { opacity: 0; }
</style>
