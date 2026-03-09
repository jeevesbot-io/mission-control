<template>
  <nav class="tasks-sidebar">
    <!-- Main sections -->
    <div class="sidebar-group">
      <button
        class="sidebar-item"
        :class="{ active: tasksStore.sidebarSection === 'all' && !tasksStore.filters.agent && !tasksStore.filters.project }"
        @click="showAll"
      >
        <McIcon name="layers" :size="15" />
        <span class="sidebar-item__label">All Tasks</span>
        <span class="sidebar-item__count mc-mono">{{ tasksStore.tasks.length }}</span>
      </button>

      <button
        class="sidebar-item"
        :class="{ active: tasksStore.sidebarSection === 'my-tasks' }"
        @click="showMyTasks"
      >
        <McIcon name="user" :size="15" />
        <span class="sidebar-item__label">My Tasks</span>
        <span class="sidebar-item__count mc-mono">{{ myTasksCount }}</span>
      </button>
    </div>

    <!-- Status filter shortcuts -->
    <div class="sidebar-group">
      <div class="sidebar-group__title">Status</div>
      <button
        v-for="status in statuses"
        :key="status.value"
        class="sidebar-item sidebar-item--compact"
        :class="{ active: tasksStore.filters.status === status.value }"
        @click="filterByStatus(status.value)"
      >
        <span class="status-dot" :style="{ background: status.color }" />
        <span class="sidebar-item__label">{{ status.label }}</span>
        <span class="sidebar-item__count mc-mono">{{ statusCounts[status.value] || 0 }}</span>
      </button>
    </div>

    <!-- By Agent -->
    <div class="sidebar-group">
      <button class="sidebar-group__title sidebar-group__toggle" @click="agentsExpanded = !agentsExpanded">
        <McIcon :name="agentsExpanded ? 'chevron-down' : 'chevron-right'" :size="12" />
        By Agent
      </button>
      <template v-if="agentsExpanded">
        <button
          v-for="agent in agentItems"
          :key="agent.name"
          class="sidebar-item sidebar-item--compact sidebar-item--nested"
          :class="{ active: tasksStore.filters.agent === agent.name }"
          @click="filterByAgent(agent.name)"
        >
          <McIcon name="bot" :size="13" />
          <span class="sidebar-item__label">{{ agent.name }}</span>
          <span class="sidebar-item__count mc-mono">{{ agent.count }}</span>
        </button>
        <div v-if="agentItems.length === 0" class="sidebar-empty">No agents</div>
      </template>
    </div>

    <!-- By Project -->
    <div class="sidebar-group">
      <button class="sidebar-group__title sidebar-group__toggle" @click="projectsExpanded = !projectsExpanded">
        <McIcon :name="projectsExpanded ? 'chevron-down' : 'chevron-right'" :size="12" />
        By Project
      </button>
      <template v-if="projectsExpanded">
        <button
          v-for="proj in projectItems"
          :key="proj.id"
          class="sidebar-item sidebar-item--compact sidebar-item--nested"
          :class="{ active: tasksStore.filters.project === proj.id }"
          @click="filterByProject(proj.id)"
        >
          <McIcon name="folder" :size="13" />
          <span class="sidebar-item__label">{{ proj.name }}</span>
          <span class="sidebar-item__count mc-mono">{{ proj.count }}</span>
        </button>
        <button
          class="sidebar-item sidebar-item--compact sidebar-item--nested"
          :class="{ active: tasksStore.filters.project === 'untagged' }"
          @click="filterByProject('untagged')"
        >
          <McIcon name="inbox" :size="13" />
          <span class="sidebar-item__label">No Project</span>
          <span class="sidebar-item__count mc-mono">{{ noProjectCount }}</span>
        </button>
        <div v-if="projectItems.length === 0 && noProjectCount === 0" class="sidebar-empty">No projects</div>
      </template>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import McIcon from '@/components/ui/McIcon.vue'
import { useTasksStore, STATUS_ORDER, STATUS_LABELS, STATUS_COLORS } from '../store'
import type { TaskStatus } from '../store'

const tasksStore = useTasksStore()

const agentsExpanded = ref(true)
const projectsExpanded = ref(true)

const statuses = STATUS_ORDER.map((s) => ({
  value: s,
  label: STATUS_LABELS[s],
  color: STATUS_COLORS[s],
}))

const statusCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const t of tasksStore.tasks) {
    counts[t.status] = (counts[t.status] || 0) + 1
  }
  return counts
})

const myTasksCount = computed(() =>
  tasksStore.tasks.filter((t) => t.status === 'todo' || t.status === 'in-progress').length,
)

const agentItems = computed(() =>
  Object.entries(tasksStore.groupedByAgent)
    .filter(([name]) => name !== 'unassigned')
    .map(([name, tasks]) => ({ name, count: tasks.length }))
    .sort((a, b) => b.count - a.count),
)

const projectItems = computed(() =>
  tasksStore.projects.map((p) => ({
    id: p.id,
    name: p.name,
    count: tasksStore.tasks.filter((t) => t.project === p.id).length,
  })).filter((p) => p.count > 0),
)

const noProjectCount = computed(() =>
  tasksStore.tasks.filter((t) => !t.project).length,
)

function showAll() {
  tasksStore.clearFilters()
  tasksStore.sidebarSection = 'all'
}

function showMyTasks() {
  tasksStore.clearFilters()
  tasksStore.sidebarSection = 'my-tasks'
  // Filter to active work
  tasksStore.setFilter('status', null)
}

function filterByStatus(status: TaskStatus) {
  tasksStore.clearFilters()
  tasksStore.setFilter('status', status)
}

function filterByAgent(agent: string) {
  tasksStore.clearFilters()
  tasksStore.setFilter('agent', agent)
  tasksStore.sidebarSection = 'by-agent'
}

function filterByProject(projectId: string) {
  tasksStore.clearFilters()
  tasksStore.setFilter('project', projectId)
  tasksStore.sidebarSection = 'by-project'
}
</script>

<style scoped>
.tasks-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem 0;
  height: 100%;
  overflow-y: auto;
}

.sidebar-group {
  display: flex;
  flex-direction: column;
  padding: 0 0.5rem;
  margin-bottom: 0.5rem;
}

.sidebar-group__title {
  font-size: var(--mc-text-xs);
  font-weight: 600;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.4rem 0.5rem 0.25rem;
  background: none;
  border: none;
}

.sidebar-group__toggle {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  cursor: pointer;
  transition: color var(--mc-transition-speed);
}

.sidebar-group__toggle:hover {
  color: var(--mc-text);
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  border-radius: var(--mc-radius-sm);
  background: transparent;
  border: none;
  color: var(--mc-text-muted);
  font-size: var(--mc-text-sm);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
  width: 100%;
  text-align: left;
}

.sidebar-item:hover {
  background: var(--mc-bg-hover);
  color: var(--mc-text);
}

.sidebar-item.active {
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
}

.sidebar-item--compact {
  padding: 0.3rem 0.5rem;
  font-size: var(--mc-text-xs);
}

.sidebar-item--nested {
  padding-left: 1.25rem;
}

.sidebar-item__label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-item__count {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
  background: var(--mc-bg-hover);
  padding: 0 5px;
  border-radius: var(--mc-radius-full);
  min-width: 18px;
  text-align: center;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.sidebar-empty {
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
  padding: 0.3rem 1.25rem;
  opacity: 0.6;
}
</style>
