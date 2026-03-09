<template>
  <div class="tasks-list" @keydown="handleKeydown" tabindex="0" ref="listRef">
    <div
      v-for="(task, index) in tasksStore.sortedTasks"
      :key="task.id"
      class="task-row"
      :class="{
        'task-row--selected': task.id === tasksStore.selectedTaskId,
        'task-row--focused': index === focusedIndex,
        'task-row--done': task.status === 'done',
        'task-row--blocked': tasksStore.isTaskBlocked(task),
      }"
      @click="emit('select', task)"
    >
      <!-- Priority dot -->
      <div class="task-row__priority" @click.stop="togglePriorityMenu(index, $event)">
        <span class="priority-dot" :style="{ background: PRIORITY_COLORS[task.priority] }" :title="task.priority" />
        <!-- Priority dropdown -->
        <Transition name="fade">
          <div v-if="priorityMenuIndex === index" class="inline-menu" :style="menuPosition">
            <button
              v-for="p in PRIORITY_ORDER"
              :key="p"
              class="inline-menu__item"
              @click.stop="changePriority(task, p)"
            >
              <span class="priority-dot" :style="{ background: PRIORITY_COLORS[p] }" />
              {{ PRIORITY_LABELS[p] }}
            </button>
          </div>
        </Transition>
      </div>

      <!-- Title -->
      <span class="task-row__title">{{ task.title }}</span>

      <!-- Agent badge -->
      <McChip v-if="task.skill" color="purple" mono size="sm">
        {{ task.skill }}
      </McChip>

      <!-- Tags -->
      <McChip
        v-for="tag in task.tags.slice(0, 2)"
        :key="tag"
        mono
        size="sm"
      >
        {{ tag }}
      </McChip>
      <McChip v-if="task.tags.length > 2" mono size="sm">
        +{{ task.tags.length - 2 }}
      </McChip>

      <!-- Status badge -->
      <div class="task-row__status" @click.stop="toggleStatusMenu(index, $event)">
        <McChip
          :color="statusChipColor(task.status)"
          variant="status"
          mono
          uppercase
          size="sm"
          dot
        >
          {{ STATUS_LABELS[task.status] }}
        </McChip>
        <!-- Status dropdown -->
        <Transition name="fade">
          <div v-if="statusMenuIndex === index" class="inline-menu" :style="menuPosition">
            <button
              v-for="s in STATUS_ORDER"
              :key="s"
              class="inline-menu__item"
              :class="{ active: task.status === s }"
              @click.stop="changeStatus(task, s)"
            >
              <span class="status-dot" :style="{ background: STATUS_COLORS[s] }" />
              {{ STATUS_LABELS[s] }}
            </button>
          </div>
        </Transition>
      </div>

      <!-- Updated time -->
      <span class="task-row__time mc-mono">{{ relativeTime(task.updatedAt) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import McChip from '@/components/ui/McChip.vue'
import { useTasksStore } from '../store'
import type { Task, TaskStatus, TaskPriority } from '../store'
import {
  STATUS_ORDER,
  STATUS_LABELS,
  STATUS_COLORS,
  PRIORITY_ORDER,
  PRIORITY_LABELS,
  PRIORITY_COLORS,
} from '../store'

const emit = defineEmits<{ select: [task: Task] }>()
const tasksStore = useTasksStore()

const _listRef = ref<HTMLElement>()
const focusedIndex = ref(-1)
const statusMenuIndex = ref<number | null>(null)
const priorityMenuIndex = ref<number | null>(null)
const menuPosition = ref<Record<string, string>>({})

function statusChipColor(status: TaskStatus): string {
  const map: Record<TaskStatus, string> = {
    backlog: 'blue',
    todo: 'blue',
    'in-progress': 'amber',
    done: 'green',
  }
  return map[status] || 'blue'
}

function relativeTime(dateStr: string): string {
  if (!dateStr) return ''
  const ms = Date.now() - new Date(dateStr).getTime()
  const min = Math.floor(ms / 60_000)
  if (min < 1) return 'now'
  if (min < 60) return `${min}m`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h}h`
  const d = Math.floor(h / 24)
  return `${d}d`
}

function toggleStatusMenu(index: number, event: MouseEvent) {
  priorityMenuIndex.value = null
  if (statusMenuIndex.value === index) {
    statusMenuIndex.value = null
    return
  }
  statusMenuIndex.value = index
  positionMenu(event)
}

function togglePriorityMenu(index: number, event: MouseEvent) {
  statusMenuIndex.value = null
  if (priorityMenuIndex.value === index) {
    priorityMenuIndex.value = null
    return
  }
  priorityMenuIndex.value = index
  positionMenu(event)
}

function positionMenu(event: MouseEvent) {
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  menuPosition.value = {
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    position: 'fixed',
  }
}

async function changeStatus(task: Task, status: TaskStatus) {
  statusMenuIndex.value = null
  if (task.status !== status) {
    await tasksStore.moveTask(task.id, status)
  }
}

async function changePriority(task: Task, priority: TaskPriority) {
  priorityMenuIndex.value = null
  if (task.priority !== priority) {
    await tasksStore.updateTask(task.id, { priority })
  }
}

function handleKeydown(e: KeyboardEvent) {
  const len = tasksStore.sortedTasks.length
  if (!len) return

  if (e.key === 'ArrowDown' || e.key === 'j') {
    e.preventDefault()
    focusedIndex.value = Math.min(focusedIndex.value + 1, len - 1)
  } else if (e.key === 'ArrowUp' || e.key === 'k') {
    e.preventDefault()
    focusedIndex.value = Math.max(focusedIndex.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const focused = tasksStore.sortedTasks[focusedIndex.value]
    if (focusedIndex.value >= 0 && focusedIndex.value < len && focused) {
      emit('select', focused)
    }
  }
}

// Close menus on outside click
function handleOutsideClick() {
  statusMenuIndex.value = null
  priorityMenuIndex.value = null
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style scoped>
.tasks-list {
  flex: 1;
  overflow-y: auto;
  outline: none;
}

.task-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  cursor: pointer;
  transition: background var(--mc-transition-fast);
}

.task-row:hover {
  background: var(--mc-bg-hover);
}

.task-row--selected {
  background: var(--mc-accent-subtle);
  border-left: 2px solid var(--mc-accent);
}

.task-row--focused {
  background: var(--mc-bg-hover);
  outline: 1px solid var(--mc-border-strong);
  outline-offset: -1px;
}

.task-row--done {
  opacity: 0.55;
}

.task-row--blocked {
  opacity: 0.5;
}

/* Priority dot */
.task-row__priority {
  position: relative;
  cursor: pointer;
  padding: 4px;
  flex-shrink: 0;
}

.priority-dot {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Title */
.task-row__title {
  flex: 1;
  font-size: var(--mc-text-sm);
  font-weight: 500;
  color: var(--mc-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

/* Status badge wrapper */
.task-row__status {
  position: relative;
  cursor: pointer;
  flex-shrink: 0;
}

/* Updated time */
.task-row__time {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
  flex-shrink: 0;
  min-width: 24px;
  text-align: right;
}

/* Inline menus */
.inline-menu {
  z-index: var(--mc-z-dropdown);
  background: var(--mc-surface-popover);
  border: 1px solid var(--mc-popover-border);
  border-radius: var(--mc-radius-sm);
  box-shadow: var(--mc-shadow-lg);
  padding: 0.25rem;
  min-width: 140px;
  backdrop-filter: blur(12px);
}

.inline-menu__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.35rem 0.6rem;
  border: none;
  background: transparent;
  color: var(--mc-text);
  font-size: var(--mc-text-xs);
  cursor: pointer;
  border-radius: var(--mc-radius-xs);
  transition: background var(--mc-transition-fast);
}

.inline-menu__item:hover {
  background: var(--mc-bg-hover);
}

.inline-menu__item.active {
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--mc-transition-fast);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
