<template>
  <div class="task-board">
    <!-- Filters bar -->
    <div class="board-filters">
      <div class="filters-row">
        <TagFilter />
        <div class="priority-filters">
          <button
            v-for="p in priorityOptions"
            :key="p.value"
            class="prio-chip"
            :class="{ 'prio-chip--active': activePriority === p.value }"
            @click="togglePriority(p.value)"
          >
            {{ p.label }}
          </button>
        </div>
        <label class="hide-blocked-toggle">
          <input type="checkbox" v-model="hideBlocked" />
          <span>Hide Blocked</span>
        </label>
      </div>
    </div>

    <!-- Sprint lane (P1 tasks) -->
    <div v-if="sprintTasks.length > 0" class="sprint-lane">
      <div class="sprint-header">
        <span class="sprint-title">🎯 This Sprint</span>
        <span class="sprint-count">{{ sprintTasks.length }}</span>
      </div>
      <div class="sprint-scroll">
        <TaskCard
          v-for="task in sprintTasks"
          :key="task.id"
          :task="task"
          class="sprint-card"
          @click="openDialog"
        />
      </div>
    </div>

    <!-- Columns -->
    <div class="board-columns">
      <!-- Backlog (draggable, grouped by domain) -->
      <div class="column">
        <div class="column-header">
          <span class="column-title">Backlog</span>
          <span class="column-count">{{ backlogTasks.length }}</span>
        </div>
        <VueDraggable
          v-model="backlogTasks"
          group="tasks"
          class="column-body"
          data-status="backlog"
          ghost-class="drag-ghost"
          drag-class="dragging"
          @end="onDragEnd"
        >
          <template v-for="(group, idx) in backlogGroups" :key="group.domain">
            <div class="domain-header" v-if="backlogGroups.length > 1">
              <span class="domain-label">{{ group.domain }}</span>
              <span class="domain-count">{{ group.tasks.length }}</span>
            </div>
            <TaskCard
              v-for="task in group.tasks"
              :key="task.id"
              :task="task"
              @click="openDialog"
            />
          </template>
        </VueDraggable>
        <button class="quick-add-btn" @click="openNewTask('backlog')">+ Add task</button>
      </div>

      <!-- Todo (draggable) -->
      <div class="column">
        <div class="column-header">
          <span class="column-title">Todo</span>
          <span class="column-count">{{ todoTasks.length }}</span>
          <HeartbeatStatus class="heartbeat-inline" />
        </div>
        <VueDraggable
          v-model="todoTasks"
          group="tasks"
          class="column-body"
          data-status="todo"
          ghost-class="drag-ghost"
          drag-class="dragging"
          @end="onDragEnd"
        >
          <TaskCard
            v-for="task in todoTasks"
            :key="task.id"
            :task="task"
            @click="openDialog"
          />
        </VueDraggable>
        <button class="quick-add-btn" @click="openNewTask('todo')">+ Add task</button>
      </div>

      <!-- In Progress (read-only — agent controlled) -->
      <div class="column column-agent">
        <div class="column-header">
          <span class="column-title">In Progress</span>
          <span class="column-count">{{ inProgressTasks.length }}</span>
          <span class="agent-badge">agent</span>
        </div>
        <div class="column-body static-list">
          <TaskCard
            v-for="task in inProgressTasks"
            :key="task.id"
            :task="task"
            @click="openDialog"
          />
        </div>
      </div>

      <!-- Done (read-only — agent controlled) -->
      <div class="column column-agent">
        <div class="column-header">
          <span class="column-title">Done</span>
          <span class="column-count">{{ doneTasks.length }}</span>
          <span class="agent-badge">agent</span>
        </div>
        <div class="column-body static-list">
          <TaskCard
            v-for="task in doneTasks"
            :key="task.id"
            :task="task"
            @click="openDialog"
          />
        </div>
      </div>
    </div>

    <!-- Task Dialog -->
    <TaskDialog
      v-model="dialogOpen"
      :task="editingTask"
      @save="onSave"
      @delete="onDelete"
      @add-reference="onAddRef"
      @delete-reference="onDeleteRef"
      @run="onRun"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { useWarRoomStore } from '../store'
import type { Task, Reference } from '../store'
import TaskCard from './TaskCard.vue'
import TaskDialog from './TaskDialog.vue'
import TagFilter from './TagFilter.vue'
import HeartbeatStatus from './HeartbeatStatus.vue'

const store = useWarRoomStore()

const hideBlocked = ref(false)
const activePriority = ref<string | null>(null)

const priorityOptions = [
  { label: 'P1', value: 'urgent' },
  { label: 'P2', value: 'high' },
  { label: 'P3', value: 'medium' },
  { label: 'P4', value: 'low' },
]

function togglePriority(value: string) {
  if (activePriority.value === value) {
    activePriority.value = null
    store.setPriorityFilter(null)
  } else {
    activePriority.value = value
    store.setPriorityFilter(value)
  }
}

// Domain detection for backlog grouping
const DOMAIN_KEYWORDS: Record<string, string[]> = {
  'mission-control': ['mission control', 'mc-', 'dashboard', 'warroom', 'war room'],
  'openclaw': ['openclaw', 'gateway', 'plugin', 'skill'],
  'matron': ['matron', 'daily', 'memory', 'heartbeat'],
  'foundry': ['foundry', 'builder', 'scout', 'blacksmith'],
  'sports': ['sports', 'football', 'f1', 'rugby', 'premier league'],
  'archivist': ['archivist', 'archive', 'obsidian', 'note'],
  'infra': ['infra', 'deploy', 'ci/cd', 'docker', 'server', 'postgres'],
  'social': ['social', 'twitter', 'linkedin', 'post', 'content'],
}

function detectDomain(title: string): string {
  const lower = title.toLowerCase()
  for (const [domain, keywords] of Object.entries(DOMAIN_KEYWORDS)) {
    if (keywords.some(k => lower.includes(k))) return domain
  }
  return 'general'
}

interface DomainGroup {
  domain: string
  tasks: Task[]
}

const backlogGroups = computed<DomainGroup[]>(() => {
  const groups: Record<string, Task[]> = {}
  for (const task of backlogTasks.value) {
    const domain = detectDomain(task.title)
    if (!groups[domain]) groups[domain] = []
    groups[domain].push(task)
  }
  return Object.entries(groups)
    .map(([domain, tasks]) => ({ domain, tasks }))
    .sort((a, b) => b.tasks.length - a.tasks.length)
})

// Sprint lane: all P1/urgent tasks across all statuses
const sprintTasks = computed(() => {
  return store.tasks.filter(t => t.priority === 'urgent' && t.status !== 'done')
})

function filterBlocked(tasks: Task[]): Task[] {
  if (!hideBlocked.value) return tasks
  return tasks.filter((t) => !store.isTaskBlocked(t))
}

// Local ref arrays for DnD — synced from store.tasksByStatus
const backlogTasks = ref<Task[]>([])
const todoTasks = ref<Task[]>([])
const inProgressTasks = computed(() => filterBlocked(store.tasksByStatus['in-progress']))
const doneTasks = computed(() => store.tasksByStatus['done'])

// Keep local DnD arrays in sync with store (e.g. after fetch or filter change)
watch(
  [() => store.tasksByStatus, hideBlocked],
  ([val]) => {
    backlogTasks.value = [...filterBlocked(val.backlog)]
    todoTasks.value = [...filterBlocked(val.todo)]
  },
  { immediate: true, deep: true },
)

// Drag end — item has data-task-id; target container has data-status attribute
function onDragEnd(evt: { item: HTMLElement; to: HTMLElement; from: HTMLElement }) {
  const taskId = (evt.item as HTMLElement).dataset.taskId
  const targetStatus = (evt.to as HTMLElement).dataset.status as Task['status'] | undefined
  const sourceStatus = (evt.from as HTMLElement).dataset.status as Task['status'] | undefined

  if (!taskId || !targetStatus || targetStatus === sourceStatus) return
  store.moveTask(taskId, targetStatus)
}

// Dialog
const dialogOpen = ref(false)
const editingTask = ref<Task | null>(null)

function openDialog(task: Task) {
  editingTask.value = task
  dialogOpen.value = true
}

function openNewTask(status: Task['status']) {
  editingTask.value = null
  // Pre-set status in dialog via a synthetic partial task
  editingTask.value = { status } as Task
  dialogOpen.value = true
}

async function onSave(payload: Partial<Task>) {
  if (editingTask.value?.id) {
    await store.updateTask(editingTask.value.id, payload)
  } else {
    await store.createTask(payload)
  }
}

async function onDelete(id: string | undefined) {
  if (id) {
    await store.deleteTask(id)
    dialogOpen.value = false
  }
}

async function onAddRef(ref: Omit<Reference, 'id' | 'createdAt'>) {
  if (editingTask.value?.id) {
    await store.addReference(editingTask.value.id, ref)
  }
}

async function onDeleteRef(refId: string) {
  if (editingTask.value?.id) {
    await store.deleteReference(editingTask.value.id, refId)
  }
}

async function onRun(id: string) {
  await store.runTask(id)
  dialogOpen.value = false
}
</script>

<style scoped>
.task-board { display: flex; flex-direction: column; gap: 1rem; height: 100%; }

.board-filters {
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--mc-border);
}

.filters-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.priority-filters {
  display: flex;
  gap: 0.25rem;
}

.prio-chip {
  padding: 0.2rem 0.55rem;
  font-size: 0.68rem;
  font-weight: 600;
  font-family: var(--mc-font-mono);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-full);
  background: var(--mc-bg-surface);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-fast);
}
.prio-chip:hover { border-color: var(--mc-border-strong); color: var(--mc-text); }
.prio-chip--active {
  background: var(--mc-accent);
  border-color: var(--mc-accent);
  color: #000;
}

.hide-blocked-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  cursor: pointer;
  user-select: none;
}
.hide-blocked-toggle input { cursor: pointer; }

.board-columns {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.column {
  display: flex;
  flex-direction: column;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
  min-height: 300px;
}

.column-agent {
  opacity: 0.9;
  border-style: dashed;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--mc-border);
  flex-shrink: 0;
}

.column-title {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
}

.column-count {
  font-size: 0.7rem;
  font-family: var(--mc-font-mono);
  background: var(--mc-bg-hover);
  color: var(--mc-text-muted);
  padding: 1px 6px;
  border-radius: 10px;
}

.agent-badge {
  margin-left: auto;
  font-size: 0.6rem;
  font-family: var(--mc-font-mono);
  text-transform: uppercase;
  color: var(--mc-text-muted);
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border);
  padding: 1px 5px;
  border-radius: 3px;
}

.heartbeat-inline { margin-left: auto; }

.column-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.static-list {
  /* Non-draggable columns */
}

.quick-add-btn {
  width: 100%;
  padding: 0.4rem;
  border: none;
  background: none;
  color: var(--mc-text-muted);
  font-size: 0.73rem;
  cursor: pointer;
  border-top: 1px solid var(--mc-border);
  transition: color var(--mc-transition-speed);
  flex-shrink: 0;
}
.quick-add-btn:hover { color: var(--mc-accent); }

/* Sprint lane */
.sprint-lane {
  background: var(--mc-bg-surface);
  border: 1px solid color-mix(in srgb, var(--mc-accent) 30%, var(--mc-border));
  border-radius: var(--mc-radius);
  overflow: hidden;
}
.sprint-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--mc-border);
  background: color-mix(in srgb, var(--mc-accent) 5%, transparent);
}
.sprint-title {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.sprint-count {
  font-size: 0.68rem;
  font-family: var(--mc-font-mono);
  background: var(--mc-accent);
  color: #000;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 700;
}
.sprint-scroll {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  overflow-x: auto;
}
.sprint-card {
  min-width: 220px;
  max-width: 280px;
  flex-shrink: 0;
}

/* Domain grouping */
.domain-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.25rem 0.15rem;
  margin-top: 0.25rem;
}
.domain-label {
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--mc-text-muted);
}
.domain-count {
  font-size: 0.58rem;
  font-family: var(--mc-font-mono);
  background: var(--mc-bg-hover);
  color: var(--mc-text-muted);
  padding: 0 4px;
  border-radius: 8px;
}

/* DnD visual feedback */
:deep(.drag-ghost) {
  opacity: 0.3;
  background: var(--mc-accent-subtle);
  border: 1px dashed var(--mc-accent);
}
:deep(.dragging) {
  opacity: 0.9;
  transform: rotate(1deg);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
</style>
