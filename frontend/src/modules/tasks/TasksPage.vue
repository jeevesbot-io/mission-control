<template>
  <PageShell>
    <div class="tasks-page">
      <!-- Left sidebar -->
      <TasksSidebar class="tasks-page__sidebar" />

      <!-- Main content area -->
      <div class="tasks-page__main">
        <!-- Header bar -->
        <div class="tasks-header">
          <div class="tasks-header__left">
            <h1 class="tasks-header__title">Tasks</h1>
            <span class="tasks-header__count mc-mono">{{ tasksStore.filteredTasks.length }}</span>
          </div>
          <div class="tasks-header__right">
            <!-- Sort selector -->
            <div class="sort-selector">
              <McIcon name="arrow-up-down" :size="13" />
              <select v-model="tasksStore.sortField" class="sort-select">
                <option value="updated">Updated</option>
                <option value="priority">Priority</option>
                <option value="created">Created</option>
              </select>
            </div>
            <!-- View mode toggle -->
            <div class="view-toggle">
              <button
                class="view-toggle__btn"
                :class="{ active: tasksStore.viewMode === 'list' }"
                @click="tasksStore.viewMode = 'list'"
                title="List view"
              >
                <McIcon name="list" :size="16" />
              </button>
              <button
                class="view-toggle__btn"
                :class="{ active: tasksStore.viewMode === 'kanban' }"
                @click="tasksStore.viewMode = 'kanban'"
                title="Kanban view"
              >
                <McIcon name="kanban" :size="16" />
              </button>
            </div>
            <!-- Create button -->
            <McButton variant="primary" size="sm" icon="plus" @click="showCreateModal = true">
              New Task
            </McButton>
          </div>
        </div>

        <!-- Active filters bar -->
        <div v-if="hasActiveFilters" class="active-filters">
          <McChip
            v-if="tasksStore.filters.status"
            color="blue"
            removable
            mono
            uppercase
            @remove="tasksStore.setFilter('status', null)"
          >
            {{ tasksStore.filters.status }}
          </McChip>
          <McChip
            v-if="tasksStore.filters.priority"
            :color="priorityChipColor(tasksStore.filters.priority)"
            removable
            mono
            uppercase
            @remove="tasksStore.setFilter('priority', null)"
          >
            {{ tasksStore.filters.priority }}
          </McChip>
          <McChip
            v-if="tasksStore.filters.agent"
            color="purple"
            removable
            mono
            @remove="tasksStore.setFilter('agent', null)"
          >
            {{ tasksStore.filters.agent }}
          </McChip>
          <McChip
            v-if="tasksStore.filters.project"
            color="cyan"
            removable
            mono
            @remove="tasksStore.setFilter('project', null)"
          >
            {{ tasksStore.getProjectName(tasksStore.filters.project) }}
          </McChip>
          <button class="clear-filters-btn" @click="tasksStore.clearFilters()">Clear all</button>
        </div>

        <!-- Content -->
        <McLoadingState v-if="tasksStore.loading" label="Loading tasks…" />
        <McEmptyState
          v-else-if="tasksStore.filteredTasks.length === 0"
          icon="check-square"
          title="No tasks found"
          description="Create a task or adjust your filters."
          cta-label="New Task"
          @cta-click="showCreateModal = true"
        />
        <template v-else>
          <TasksList
            v-if="tasksStore.viewMode === 'list'"
            @select="selectTask"
          />
          <TasksKanban
            v-else
            @select="selectTask"
          />
        </template>
      </div>

      <!-- Detail slide-in panel -->
      <Transition name="slide-in-right">
        <TaskDetail
          v-if="tasksStore.selectedTask"
          :task="tasksStore.selectedTask"
          class="tasks-page__detail"
          @close="closeDetail"
          @update="onTaskUpdate"
          @delete="onTaskDelete"
        />
      </Transition>

      <!-- Create modal -->
      <TaskCreateModal
        v-if="showCreateModal"
        @close="showCreateModal = false"
        @created="onTaskCreated"
      />
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import McButton from '@/components/ui/McButton.vue'
import McChip from '@/components/ui/McChip.vue'
import McLoadingState from '@/components/ui/McLoadingState.vue'
import McEmptyState from '@/components/ui/McEmptyState.vue'
import { useTasksStore } from './store'
import type { Task, TaskPriority } from './store'
import TasksSidebar from './components/TasksSidebar.vue'
import TasksList from './components/TasksList.vue'
import TasksKanban from './components/TasksKanban.vue'
import TaskDetail from './components/TaskDetail.vue'
import TaskCreateModal from './components/TaskCreateModal.vue'

const route = useRoute()
const router = useRouter()
const tasksStore = useTasksStore()

const showCreateModal = ref(false)

const hasActiveFilters = computed(() =>
  tasksStore.filters.project ||
  tasksStore.filters.priority ||
  tasksStore.filters.status ||
  tasksStore.filters.agent ||
  tasksStore.filters.tags.length > 0,
)

function priorityChipColor(p: TaskPriority): string {
  const map: Record<TaskPriority, string> = { urgent: 'red', high: 'orange', medium: 'amber', low: 'blue' }
  return map[p] || 'blue'
}

// URL-driven state
watch(
  () => route.params.id,
  (id) => {
    tasksStore.selectedTaskId = (id as string) || null
  },
  { immediate: true },
)

watch(
  () => route.query,
  (query) => {
    if (query.agent) tasksStore.setFilter('agent', query.agent as string)
    if (query.project) tasksStore.setFilter('project', query.project as string)
    if (query.status) tasksStore.setFilter('status', query.status as string)
    if (query.priority) tasksStore.setFilter('priority', query.priority as string)
  },
  { immediate: true },
)

function selectTask(task: Task) {
  router.push({ name: 'task-detail', params: { id: task.id } })
}

function closeDetail() {
  router.push({ name: 'tasks' })
}

async function onTaskUpdate(id: string, payload: Partial<Task>) {
  await tasksStore.updateTask(id, payload)
}

async function onTaskDelete(id: string) {
  await tasksStore.deleteTask(id)
  closeDetail()
}

function onTaskCreated() {
  showCreateModal.value = false
}

// Keyboard shortcuts
function isInputFocused(): boolean {
  const el = document.activeElement
  if (!el) return false
  const tag = el.tagName.toLowerCase()
  return tag === 'input' || tag === 'textarea' || tag === 'select' || (el as HTMLElement).isContentEditable
}

function handleKeyboard(e: KeyboardEvent) {
  if (e.key === 'c' && !isInputFocused() && !e.metaKey && !e.ctrlKey) {
    e.preventDefault()
    showCreateModal.value = true
  }
  if (e.key === 'Escape') {
    if (showCreateModal.value) {
      showCreateModal.value = false
    } else if (tasksStore.selectedTaskId) {
      closeDetail()
    }
  }
}

onMounted(() => {
  tasksStore.fetchAll()
  document.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyboard)
})
</script>

<style scoped>
.tasks-page {
  display: flex;
  height: calc(100vh - var(--mc-header-height) - var(--mc-page-padding) * 2);
  gap: 0;
  overflow: hidden;
}

.tasks-page__sidebar {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--mc-border);
}

.tasks-page__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tasks-page__detail {
  width: 420px;
  flex-shrink: 0;
  border-left: 1px solid var(--mc-border);
}

/* Header */
.tasks-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  flex-shrink: 0;
}

.tasks-header__left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tasks-header__title {
  font-family: var(--mc-font-display);
  font-size: var(--mc-text-lg);
  font-weight: 700;
  margin: 0;
}

.tasks-header__count {
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
  background: var(--mc-bg-hover);
  padding: 1px 7px;
  border-radius: var(--mc-radius-full);
}

.tasks-header__right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Sort selector */
.sort-selector {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--mc-text-muted);
}

.sort-select {
  background: transparent;
  border: none;
  color: var(--mc-text-muted);
  font-size: var(--mc-text-xs);
  font-family: var(--mc-font-mono);
  cursor: pointer;
  outline: none;
}

.sort-select option {
  background: var(--mc-bg-elevated);
  color: var(--mc-text);
}

/* View toggle */
.view-toggle {
  display: flex;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  overflow: hidden;
}

.view-toggle__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 28px;
  background: transparent;
  border: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}

.view-toggle__btn:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
}

.view-toggle__btn.active {
  color: var(--mc-accent);
  background: var(--mc-accent-subtle);
}

/* Active filters */
.active-filters {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  flex-shrink: 0;
}

.clear-filters-btn {
  background: none;
  border: none;
  color: var(--mc-text-muted);
  font-size: var(--mc-text-xs);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: var(--mc-radius-xs);
  transition: color var(--mc-transition-speed);
}

.clear-filters-btn:hover {
  color: var(--mc-danger);
}

/* Slide-in transition */
.slide-in-right-enter-active,
.slide-in-right-leave-active {
  transition: transform var(--mc-transition-slow) var(--mc-ease-out);
}

.slide-in-right-enter-from {
  transform: translateX(100%);
}

.slide-in-right-leave-to {
  transform: translateX(100%);
}
</style>
