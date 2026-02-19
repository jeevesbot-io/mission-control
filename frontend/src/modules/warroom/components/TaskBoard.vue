<template>
  <div class="task-board">
    <!-- Filters bar -->
    <div class="board-filters">
      <div class="filters-row">
        <ProjectFilter />
        <TagFilter />
        <label class="hide-blocked-toggle">
          <input type="checkbox" v-model="hideBlocked" />
          <span>Hide Blocked</span>
        </label>
      </div>
    </div>

    <!-- Columns -->
    <div class="board-columns">
      <!-- Backlog (draggable) -->
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
          <TaskCard
            v-for="task in backlogTasks"
            :key="task.id"
            :task="task"
            @click="openDialog"
          />
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
import ProjectFilter from './ProjectFilter.vue'
import TagFilter from './TagFilter.vue'
import HeartbeatStatus from './HeartbeatStatus.vue'

const store = useWarRoomStore()

const hideBlocked = ref(false)

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
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.filters-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
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
  border: 1px solid rgba(255,255,255,0.06);
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
  border-bottom: 1px solid rgba(255,255,255,0.06);
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
  background: rgba(255,255,255,0.08);
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
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
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
  border-top: 1px solid rgba(255,255,255,0.06);
  transition: color var(--mc-transition-speed);
  flex-shrink: 0;
}
.quick-add-btn:hover { color: var(--mc-accent); }

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
