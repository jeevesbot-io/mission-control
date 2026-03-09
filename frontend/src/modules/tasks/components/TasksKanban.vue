<template>
  <div class="tasks-kanban">
    <div
      v-for="status in STATUS_ORDER"
      :key="status"
      class="kanban-column"
    >
      <div class="kanban-column__header">
        <span class="kanban-column__dot" :style="{ background: STATUS_COLORS[status] }" />
        <span class="kanban-column__title">{{ STATUS_LABELS[status] }}</span>
        <span class="kanban-column__count mc-mono">{{ columnTasks(status).length }}</span>
      </div>

      <VueDraggable
        v-model="columnModels[status]"
        group="tasks-kanban"
        class="kanban-column__body"
        :data-status="status"
        ghost-class="drag-ghost"
        drag-class="dragging"
        @end="onDragEnd"
      >
        <div
          v-for="task in columnModels[status]"
          :key="task.id"
          class="kanban-card"
          :class="{
            'kanban-card--done': task.status === 'done',
            'kanban-card--blocked': tasksStore.isTaskBlocked(task),
          }"
          :data-task-id="task.id"
          @click="emit('select', task)"
        >
          <div class="kanban-card__header">
            <span class="priority-dot" :style="{ background: PRIORITY_COLORS[task.priority] }" />
            <span v-if="task.skill" class="kanban-card__agent mc-mono">{{ task.skill }}</span>
          </div>
          <p class="kanban-card__title">{{ task.title }}</p>
          <div v-if="task.tags.length > 0" class="kanban-card__tags">
            <span v-for="tag in task.tags.slice(0, 2)" :key="tag" class="kanban-card__tag mc-mono">{{ tag }}</span>
          </div>
        </div>
      </VueDraggable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { useTasksStore } from '../store'
import type { Task, TaskStatus } from '../store'
import { STATUS_ORDER, STATUS_LABELS, STATUS_COLORS, PRIORITY_COLORS } from '../store'

const emit = defineEmits<{ select: [task: Task] }>()
const tasksStore = useTasksStore()

// Maintain local reactive arrays for drag-and-drop
const columnModels = reactive<Record<TaskStatus, Task[]>>({
  backlog: [],
  todo: [],
  'in-progress': [],
  done: [],
})

function columnTasks(status: TaskStatus): Task[] {
  return tasksStore.tasksByStatus[status] || []
}

// Sync from store
watch(
  () => tasksStore.tasksByStatus,
  (val) => {
    for (const status of STATUS_ORDER) {
      columnModels[status] = [...(val[status] || [])]
    }
  },
  { immediate: true, deep: true },
)

function onDragEnd(evt: { item: HTMLElement; to: HTMLElement; from: HTMLElement }) {
  const taskId = (evt.item as HTMLElement).dataset.taskId
  const targetStatus = (evt.to as HTMLElement).dataset.status as TaskStatus | undefined
  const sourceStatus = (evt.from as HTMLElement).dataset.status as TaskStatus | undefined

  if (!taskId || !targetStatus || targetStatus === sourceStatus) return
  tasksStore.moveTask(taskId, targetStatus)
}
</script>

<style scoped>
.tasks-kanban {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  flex: 1;
  overflow-x: auto;
  padding: 0.75rem 1rem;
  min-height: 0;
}

.kanban-column {
  display: flex;
  flex-direction: column;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
  min-height: 200px;
}

.kanban-column__header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.6rem;
  border-bottom: 1px solid var(--mc-border);
  flex-shrink: 0;
}

.kanban-column__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.kanban-column__title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
}

.kanban-column__count {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
  background: var(--mc-bg-hover);
  padding: 0 5px;
  border-radius: var(--mc-radius-full);
  margin-left: auto;
}

.kanban-column__body {
  flex: 1;
  overflow-y: auto;
  padding: 0.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-height: 60px;
}

/* Cards */
.kanban-card {
  background: var(--mc-bg-elevated);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  padding: 0.55rem 0.65rem;
  cursor: pointer;
  transition: background var(--mc-transition-speed), transform var(--mc-transition-speed);
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.kanban-card:hover {
  background: var(--mc-bg-hover);
  transform: translateY(-1px);
}

.kanban-card--done {
  opacity: 0.55;
}

.kanban-card--blocked {
  opacity: 0.45;
  border-left: 2px solid var(--mc-color-red);
}

.kanban-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.priority-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.kanban-card__agent {
  font-size: 0.6rem;
  color: var(--mc-color-purple);
  background: var(--mc-color-purple-bg);
  padding: 1px 5px;
  border-radius: 3px;
}

.kanban-card__title {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--mc-text);
  line-height: 1.35;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kanban-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.kanban-card__tag {
  font-size: 0.58rem;
  color: var(--mc-text-muted);
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border);
  padding: 0 4px;
  border-radius: 3px;
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
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
</style>
