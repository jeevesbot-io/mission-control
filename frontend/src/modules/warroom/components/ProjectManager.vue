<template>
  <div class="project-manager">
    <div class="pm-header">
      <button class="btn-primary" @click="openCreate">+ New Project</button>
    </div>

    <div class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        :style="{ borderLeftColor: COLOR_MAP[project.color] || '#7c6aff' }"
      >
        <div class="project-card-header">
          <span class="project-icon">{{ project.icon }}</span>
          <span class="project-name">{{ project.name }}</span>
          <span class="project-status" :class="`status-${project.status}`">{{ project.status }}</span>
        </div>
        <p v-if="project.description" class="project-desc">{{ project.description }}</p>
        <div class="project-footer">
          <span class="task-count">{{ project.task_count || 0 }} tasks</span>
          <div class="project-actions">
            <button class="btn-sm btn-secondary" @click="openEdit(project)">Edit</button>
            <button class="btn-sm btn-danger" @click="confirmDelete(project)">Delete</button>
          </div>
        </div>
      </div>

      <div v-if="projects.length === 0" class="no-projects">
        <p>No projects yet. Create one to organize your tasks.</p>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <Dialog
      v-model:visible="dialogOpen"
      :header="editing ? 'Edit Project' : 'New Project'"
      :modal="true"
      :dismissableMask="true"
      :style="{ width: '460px' }"
    >
      <div class="dialog-body">
        <div class="field">
          <label>ID</label>
          <InputText v-model="form.id" :disabled="!!editing" placeholder="project-slug" />
        </div>
        <div class="field">
          <label>Name</label>
          <InputText v-model="form.name" placeholder="Project Name" autofocus />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Icon</label>
            <InputText v-model="form.icon" placeholder="Emoji or icon name" />
          </div>
          <div class="field">
            <label>Color</label>
            <Select
              v-model="form.color"
              :options="colorOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>
        <div class="field">
          <label>Description</label>
          <Textarea v-model="form.description" placeholder="Optional description..." :rows="2" />
        </div>
        <div class="field">
          <label>Status</label>
          <Select
            v-model="form.status"
            :options="statusOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="dialogOpen = false">Cancel</button>
          <button class="btn-primary" :disabled="!form.id || !form.name" @click="save">
            {{ editing ? 'Save' : 'Create' }}
          </button>
        </div>
      </template>
    </Dialog>

    <!-- Delete Confirmation -->
    <Dialog
      v-model:visible="deleteDialogOpen"
      header="Delete Project"
      :modal="true"
      :style="{ width: '400px' }"
    >
      <p>Are you sure you want to delete <strong>{{ deletingProject?.name }}</strong>?</p>
      <p v-if="deleteError" class="delete-error">{{ deleteError }}</p>
      <template #footer>
        <button class="btn-secondary" @click="deleteDialogOpen = false">Cancel</button>
        <button class="btn-danger" @click="doDelete">Delete</button>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import { useWarRoomStore } from '../store'
import type { Project } from '../store'

const COLOR_MAP: Record<string, string> = {
  purple: '#a78bfa',
  pink: '#f472b6',
  green: '#34d399',
  blue: '#60a5fa',
  amber: '#fbbf24',
  indigo: '#818cf8',
  red: '#f87171',
  orange: '#fb923c',
  cyan: '#22d3ee',
  yellow: '#fde047',
}

const colorOptions = Object.keys(COLOR_MAP).map((c) => ({ label: c, value: c }))
const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Paused', value: 'paused' },
  { label: 'Archived', value: 'archived' },
]

const store = useWarRoomStore()
const projects = computed(() => store.projectsWithCounts)

const dialogOpen = ref(false)
const editing = ref<Project | null>(null)
const deleteDialogOpen = ref(false)
const deletingProject = ref<Project | null>(null)
const deleteError = ref('')

const defaultForm = () => ({
  id: '',
  name: '',
  icon: '',
  color: 'purple',
  description: '',
  status: 'active' as const,
  order: 0,
})

const form = ref(defaultForm())

function openCreate() {
  editing.value = null
  form.value = defaultForm()
  dialogOpen.value = true
}

function openEdit(project: Project) {
  editing.value = project
  form.value = {
    id: project.id,
    name: project.name,
    icon: project.icon,
    color: project.color,
    description: project.description || '',
    status: project.status,
    order: project.order,
  }
  dialogOpen.value = true
}

async function save() {
  if (editing.value) {
    await store.updateProject(editing.value.id, {
      name: form.value.name,
      icon: form.value.icon,
      color: form.value.color,
      description: form.value.description || null,
      status: form.value.status,
      order: form.value.order,
    })
  } else {
    await store.createProject({
      id: form.value.id,
      name: form.value.name,
      icon: form.value.icon,
      color: form.value.color,
      description: form.value.description || null,
      status: form.value.status,
      order: form.value.order,
    })
  }
  dialogOpen.value = false
  await store.fetchProjects()
}

function confirmDelete(project: Project) {
  deletingProject.value = project
  deleteError.value = ''
  deleteDialogOpen.value = true
}

async function doDelete() {
  if (!deletingProject.value) return
  const ok = await store.deleteProject(deletingProject.value.id)
  if (ok) {
    deleteDialogOpen.value = false
  } else {
    deleteError.value = store.error || 'Failed to delete project'
  }
}
</script>

<style scoped>
.pm-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.project-card {
  background: var(--mc-bg-elevated);
  border: 1px solid rgba(255,255,255,0.06);
  border-left: 4px solid;
  border-radius: var(--mc-radius-sm);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.project-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.project-icon { font-size: 1.2rem; }
.project-name { font-weight: 700; font-size: 0.9rem; flex: 1; }

.project-status {
  font-size: 0.65rem;
  font-family: var(--mc-font-mono);
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 3px;
  border: 1px solid rgba(255,255,255,0.1);
}
.status-active { color: var(--mc-success); border-color: rgba(52,211,153,0.3); }
.status-paused { color: var(--mc-warning); border-color: rgba(251,191,36,0.3); }
.status-archived { color: var(--mc-text-muted); }

.project-desc {
  font-size: 0.78rem;
  color: var(--mc-text-muted);
  margin: 0;
  line-height: 1.4;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.task-count {
  font-size: 0.7rem;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
}

.project-actions { display: flex; gap: 0.3rem; }

.no-projects {
  text-align: center;
  color: var(--mc-text-muted);
  padding: 2rem;
  grid-column: 1 / -1;
}

.dialog-body { display: flex; flex-direction: column; gap: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field label { font-size: 0.72rem; font-weight: 600; color: var(--mc-text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 0.5rem; width: 100%; }

.btn-primary {
  padding: 6px 16px;
  border-radius: var(--mc-radius-sm);
  background: var(--mc-accent);
  color: #fff;
  font-weight: 600;
  font-size: 0.82rem;
  border: none;
  cursor: pointer;
}
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  padding: 4px 10px;
  border-radius: var(--mc-radius-sm);
  background: rgba(255,255,255,0.06);
  color: var(--mc-text);
  font-size: 0.75rem;
  border: 1px solid rgba(255,255,255,0.1);
  cursor: pointer;
}

.btn-danger {
  padding: 4px 10px;
  border-radius: var(--mc-radius-sm);
  background: rgba(248,113,113,0.12);
  color: #f87171;
  font-size: 0.75rem;
  border: 1px solid rgba(248,113,113,0.3);
  cursor: pointer;
}

.btn-sm { padding: 3px 8px; font-size: 0.7rem; }

.delete-error { color: #f87171; font-size: 0.85rem; }
</style>
