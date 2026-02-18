<template>
  <div class="activity-calendar">
    <div class="calendar-header">
      <h3 class="calendar-title">Activity Calendar</h3>
      <div class="legend">
        <span class="legend-label">Less</span>
        <span class="legend-cell level-0" />
        <span class="legend-cell level-1" />
        <span class="legend-cell level-2" />
        <span class="legend-cell level-3" />
        <span class="legend-label">More</span>
      </div>
    </div>

    <div v-if="store.loading" class="calendar-loading">Loading calendar…</div>

    <div v-else class="months-grid">
      <div v-for="month in months" :key="month.label" class="month-block">
        <div class="month-label">{{ month.label }}</div>
        <div class="week-grid">
          <div
            v-for="day in month.days"
            :key="day.date"
            class="day-cell"
            :class="[`level-${day.level}`, { today: day.isToday, empty: day.empty }]"
            :title="day.empty ? '' : dayTitle(day)"
            @click="!day.empty && selectDay(day)"
          />
        </div>
      </div>
    </div>

    <!-- Day detail panel -->
    <div v-if="selectedDay" class="day-detail">
      <div class="day-detail-header">
        <span class="day-detail-date">{{ formatDate(selectedDay.date) }}</span>
        <button class="close-btn" @click="selectedDay = null">✕</button>
      </div>
      <div class="day-detail-body">
        <div class="detail-row">
          <span class="detail-icon" :class="selectedDay.memory ? 'has-memory' : 'no-memory'">
            {{ selectedDay.memory ? '●' : '○' }}
          </span>
          <span class="detail-label">Memory note {{ selectedDay.memory ? 'recorded' : 'not recorded' }}</span>
        </div>
        <div v-if="selectedDay.tasks.length" class="detail-tasks">
          <div class="detail-tasks-heading">Completed tasks ({{ selectedDay.tasks.length }})</div>
          <ul class="task-list">
            <li v-for="(t, i) in selectedDay.tasks" :key="i" class="task-item">{{ t }}</li>
          </ul>
        </div>
        <div v-else class="detail-no-tasks">No completed tasks</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useWarRoomStore } from '../store'
import type { CalendarDay } from '../store'

interface DayCell {
  date: string       // YYYY-MM-DD
  level: 0 | 1 | 2 | 3
  memory: boolean
  tasks: string[]
  isToday: boolean
  empty: boolean     // padding cell before month start
}

interface MonthBlock {
  label: string
  days: DayCell[]
}

const store = useWarRoomStore()

const selectedDay = ref<DayCell | null>(null)

const today = new Date()
const todayStr = today.toISOString().slice(0, 10)

// Build 12 months ending with the current month
const months = computed<MonthBlock[]>(() => {
  const result: MonthBlock[] = []
  const data = store.calendarData

  for (let m = 11; m >= 0; m--) {
    const d = new Date(today.getFullYear(), today.getMonth() - m, 1)
    const year = d.getFullYear()
    const month = d.getMonth()
    const label = d.toLocaleString('default', { month: 'short', year: '2-digit' })

    const daysInMonth = new Date(year, month + 1, 0).getDate()
    // getDay(): 0=Sun, we want Mon-start (0=Mon offset)
    const firstDow = (new Date(year, month, 1).getDay() + 6) % 7 // Mon=0

    const days: DayCell[] = []

    // Padding cells for days before the 1st
    for (let p = 0; p < firstDow; p++) {
      days.push({ date: '', level: 0, memory: false, tasks: [], isToday: false, empty: true })
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
      const entry: CalendarDay | undefined = data[dateStr]
      const memory = entry?.memory ?? false
      const tasks = entry?.tasks ?? []
      const activityScore = (memory ? 1 : 0) + (tasks.length > 0 ? 1 : 0) + (tasks.length > 2 ? 1 : 0)
      const level = Math.min(activityScore, 3) as 0 | 1 | 2 | 3

      days.push({
        date: dateStr,
        level,
        memory,
        tasks,
        isToday: dateStr === todayStr,
        empty: false,
      })
    }

    result.push({ label, days })
  }

  return result
})

function dayTitle(day: DayCell): string {
  const parts: string[] = [day.date]
  if (day.memory) parts.push('Memory note')
  if (day.tasks.length) parts.push(`${day.tasks.length} task${day.tasks.length > 1 ? 's' : ''} done`)
  return parts.join(' · ')
}

function selectDay(day: DayCell) {
  selectedDay.value = selectedDay.value?.date === day.date ? null : day
}

function formatDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('default', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
}

onMounted(() => store.fetchCalendar())
</script>

<style scoped>
.activity-calendar { display: flex; flex-direction: column; gap: 1rem; }

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.calendar-title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
  margin: 0;
}

.legend {
  display: flex;
  align-items: center;
  gap: 3px;
}
.legend-label { font-size: 0.65rem; color: var(--mc-text-muted); }
.legend-cell {
  width: 10px; height: 10px;
  border-radius: 2px;
}

.calendar-loading {
  color: var(--mc-text-muted);
  font-size: 0.8rem;
}

.months-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem 1.5rem;
}

.month-block {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.month-label {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
}

.week-grid {
  display: grid;
  grid-template-columns: repeat(7, 10px);
  gap: 2px;
}

.day-cell {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  cursor: pointer;
  transition: opacity var(--mc-transition-speed), transform var(--mc-transition-speed);
}

.day-cell.empty {
  cursor: default;
  background: transparent !important;
}

.day-cell:not(.empty):hover {
  opacity: 0.8;
  transform: scale(1.2);
}

.day-cell.today {
  outline: 1.5px solid var(--mc-accent);
  outline-offset: 1px;
}

/* Activity levels */
.level-0 { background: var(--mc-bg-hover, rgba(255,255,255,0.06)); }
.level-1 { background: rgba(99, 102, 241, 0.3); }  /* --mc-accent-subtle */
.level-2 { background: rgba(99, 102, 241, 0.55); }
.level-3 { background: var(--mc-accent, #6366f1); }

/* Day detail panel */
.day-detail {
  background: var(--mc-bg-surface);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--mc-radius-sm);
  overflow: hidden;
  max-width: 400px;
}

.day-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.day-detail-date {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--mc-text);
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mc-text-muted);
  font-size: 0.8rem;
  padding: 2px 4px;
}
.close-btn:hover { color: var(--mc-text); }

.day-detail-body {
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-icon { font-size: 0.9rem; }
.detail-icon.has-memory { color: var(--mc-success); }
.detail-icon.no-memory { color: var(--mc-text-muted); }
.detail-label { font-size: 0.78rem; color: var(--mc-text); }

.detail-tasks-heading {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
  margin-bottom: 0.25rem;
}

.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.task-item {
  font-size: 0.78rem;
  color: var(--mc-text);
  padding: 0.2rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.task-item:last-child { border-bottom: none; }

.detail-no-tasks {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}
</style>
