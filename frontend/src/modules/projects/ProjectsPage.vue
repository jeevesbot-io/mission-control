<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import CreateProjectDialog from './components/CreateProjectDialog.vue'
import { useProjectsStore, type Project } from './store'

const router = useRouter()
const store = useProjectsStore()

const statusFilter = ref('all')
const showCreate = ref(false)

const filteredProjects = computed(() => {
  if (statusFilter.value === 'all') return store.projects
  return store.projects.filter((p) => p.status === statusFilter.value)
})

const statusTabs = [
  { id: 'all', label: 'All' },
  { id: 'active', label: 'Active' },
  { id: 'paused', label: 'Paused' },
  { id: 'archived', label: 'Archived' },
]

function statusClass(status: string) {
  return `status-badge status-${status}`
}

function cardBorderStyle(project: Project) {
  if (!project.color) return {}
  return { borderLeftColor: project.color, borderLeftWidth: '4px', borderLeftStyle: 'solid' }
}

function goToProject(id: string) {
  router.push({ name: 'project-detail', params: { id } })
}

async function onCreated() {
  showCreate.value = false
  await store.fetchProjects()
}

onMounted(() => store.fetchProjects())
</script>

<template>
  <PageShell>
    <div class="projects-page">
      <div class="page-header">
        <h1 class="page-title">
          <McIcon name="folder-kanban" :size="24" />
          Projects
        </h1>
        <button class="btn-primary" @click="showCreate = true">
          <McIcon name="plus" :size="16" />
          New Project
        </button>
      </div>

      <!-- Status filter tabs -->
      <div class="filter-tabs">
        <button
          v-for="tab in statusTabs"
          :key="tab.id"
          class="filter-tab"
          :class="{ active: statusFilter === tab.id }"
          @click="statusFilter = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" class="loading-state">Loading projects…</div>

      <!-- Error -->
      <div v-else-if="store.error" class="error-state">{{ store.error }}</div>

      <!-- Empty state -->
      <div v-else-if="filteredProjects.length === 0" class="empty-state">
        <McIcon name="folder-kanban" :size="48" />
        <p>No {{ statusFilter === 'all' ? '' : statusFilter }} projects found</p>
      </div>

      <!-- Project grid -->
      <div v-else class="project-grid">
        <div
          v-for="project in filteredProjects"
          :key="project.id"
          class="project-card"
          :style="cardBorderStyle(project)"
          @click="goToProject(project.id)"
        >
          <div class="card-header">
            <span class="project-icon">{{ project.icon || '📂' }}</span>
            <span :class="statusClass(project.status)">{{ project.status }}</span>
          </div>
          <h3 class="project-name">{{ project.name }}</h3>
          <p v-if="project.description" class="project-desc">
            {{ project.description?.substring(0, 120) }}{{ project.description && project.description.length > 120 ? '…' : '' }}
          </p>
          <div class="card-footer">
            <span class="stat">
              <McIcon name="list-checks" :size="14" />
              {{ project.task_count }} tasks
            </span>
            <span class="stat">
              <McIcon name="users" :size="14" />
              {{ project.agent_count }} agents
            </span>
          </div>
        </div>
      </div>

      <CreateProjectDialog
        :visible="showCreate"
        @close="showCreate = false"
        @created="onCreated"
      />
    </div>
  </PageShell>
</template>

<style scoped>
.projects-page {
  max-width: 1200px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--mc-text);
  margin: 0;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  background: var(--mc-accent);
  color: #fff;
  border: none;
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: opacity var(--mc-transition-speed);
}
.btn-primary:hover {
  opacity: 0.9;
}

.filter-tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--mc-border);
  padding-bottom: 0;
}

.filter-tab {
  padding: 0.5rem 1rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--mc-text-muted);
  cursor: pointer;
  font-size: 0.875rem;
  transition: all var(--mc-transition-speed);
}
.filter-tab:hover {
  color: var(--mc-text);
}
.filter-tab.active {
  color: var(--mc-accent);
  border-bottom-color: var(--mc-accent);
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.project-card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  padding: 1.25rem;
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}
.project-card:hover {
  border-color: var(--mc-accent);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.project-icon {
  font-size: 1.5rem;
}

.status-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.status-active {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
.status-paused {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}
.status-archived {
  background: rgba(107, 114, 128, 0.15);
  color: #6b7280;
}

.project-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--mc-text);
  margin: 0 0 0.5rem;
}

.project-desc {
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  margin: 0 0 1rem;
  line-height: 1.4;
}

.card-footer {
  display: flex;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--mc-border);
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--mc-text-muted);
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  opacity: 0.6;
}
.error-state {
  color: #ef4444;
}
</style>
