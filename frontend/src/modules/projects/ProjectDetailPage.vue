<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import { useProjectsStore, type ProjectDoc } from './store'
import { useApi } from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const store = useProjectsStore()
const api = useApi()

const activeTab = ref('overview')
const editingDesc = ref(false)
const descDraft = ref('')
const editingProject = ref(false)
const editForm = ref({ name: '', icon: '', color: '', status: '' })

// Docs
const newDocTitle = ref('')
const newDocUrl = ref('')

const project = computed(() => store.selectedProject)
const projectId = computed(() => route.params.id as string)

const tabs = [
  { id: 'overview', label: 'Overview', icon: 'file-text' },
  { id: 'tasks', label: 'Tasks', icon: 'list-checks' },
  { id: 'team', label: 'Team', icon: 'users' },
]

const descriptionHtml = computed(() => {
  if (!project.value?.description) return '<em>No description</em>'
  return DOMPurify.sanitize(marked.parse(project.value.description) as string)
})

const tasksByState = computed(() => {
  if (!project.value?.tasks) return {}
  const grouped: Record<string, typeof project.value.tasks> = {}
  for (const t of project.value.tasks) {
    if (!grouped[t.state]) grouped[t.state] = []
    grouped[t.state].push(t)
  }
  return grouped
})

const stateOrder = ['in_progress', 'todo', 'backlog', 'blocked', 'peer_review', 'review', 'done', 'cancelled']

const orderedStates = computed(() => {
  const states = Object.keys(tasksByState.value)
  return stateOrder.filter((s) => states.includes(s))
})

function priorityLabel(p: number) {
  return ['', '🔴 Critical', '🟠 High', '🟡 Medium', '🟢 Low'][p] || `P${p}`
}

function stateLabel(s: string) {
  return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function startEditDesc() {
  descDraft.value = project.value?.description || ''
  editingDesc.value = true
}

async function saveDesc() {
  await store.updateProject(projectId.value, { description: descDraft.value })
  editingDesc.value = false
  await store.fetchProject(projectId.value)
}

function startEditProject() {
  if (!project.value) return
  editForm.value = {
    name: project.value.name,
    icon: project.value.icon,
    color: project.value.color,
    status: project.value.status,
  }
  editingProject.value = true
}

async function saveProject() {
  await store.updateProject(projectId.value, editForm.value)
  editingProject.value = false
  await store.fetchProject(projectId.value)
}

async function addDoc() {
  if (!newDocUrl.value) return
  const docs = [...(project.value?.docs || []), { title: newDocTitle.value || newDocUrl.value, url: newDocUrl.value }]
  await store.updateProject(projectId.value, { docs })
  newDocTitle.value = ''
  newDocUrl.value = ''
  await store.fetchProject(projectId.value)
}

async function removeDoc(index: number) {
  const docs = [...(project.value?.docs || [])]
  docs.splice(index, 1)
  await store.updateProject(projectId.value, { docs })
  await store.fetchProject(projectId.value)
}

function goBack() {
  router.push({ name: 'projects' })
}

onMounted(() => store.fetchProject(projectId.value))
watch(() => route.params.id, (id) => {
  if (id) store.fetchProject(id as string)
})
</script>

<template>
  <PageShell>
    <div class="detail-page">
      <!-- Back button -->
      <button class="back-btn" @click="goBack">
        <McIcon name="arrow-left" :size="16" />
        Projects
      </button>

      <!-- Loading -->
      <div v-if="store.loading && !project" class="loading-state">Loading…</div>

      <!-- Error -->
      <div v-else-if="store.error" class="error-state">{{ store.error }}</div>

      <template v-else-if="project">
        <!-- Header -->
        <div class="project-header">
          <div class="header-left">
            <span class="project-icon">{{ project.icon || '📂' }}</span>
            <div>
              <h1 class="project-name">{{ project.name }}</h1>
              <div class="header-meta">
                <span :class="`status-badge status-${project.status}`">{{ project.status }}</span>
                <span class="meta-stat">{{ project.task_count }} tasks</span>
                <span class="meta-stat">{{ project.agent_count }} agents</span>
              </div>
            </div>
          </div>
          <button class="btn-secondary" @click="startEditProject">
            <McIcon name="pencil" :size="14" />
            Edit
          </button>
        </div>

        <!-- Edit project modal (inline) -->
        <div v-if="editingProject" class="edit-overlay">
          <div class="edit-card">
            <h3>Edit Project</h3>
            <div class="form-row">
              <label>Name</label>
              <input v-model="editForm.name" class="mc-input" />
            </div>
            <div class="form-row">
              <label>Icon</label>
              <input v-model="editForm.icon" class="mc-input" placeholder="Emoji" />
            </div>
            <div class="form-row">
              <label>Color</label>
              <input v-model="editForm.color" type="color" class="mc-input color-input" />
            </div>
            <div class="form-row">
              <label>Status</label>
              <select v-model="editForm.status" class="mc-input">
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            <div class="form-actions">
              <button class="btn-secondary" @click="editingProject = false">Cancel</button>
              <button class="btn-primary" @click="saveProject">Save</button>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tab-bar">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="tab-btn"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            <McIcon :name="tab.icon" :size="14" />
            {{ tab.label }}
          </button>
        </div>

        <!-- Overview tab -->
        <div v-if="activeTab === 'overview'" class="tab-content">
          <section class="section">
            <div class="section-header">
              <h2 class="section-title">Description</h2>
              <button v-if="!editingDesc" class="btn-ghost" @click="startEditDesc">
                <McIcon name="pencil" :size="14" />
              </button>
            </div>
            <div v-if="editingDesc" class="desc-editor">
              <textarea v-model="descDraft" class="mc-textarea" rows="8" placeholder="Project description (Markdown supported)"></textarea>
              <div class="form-actions">
                <button class="btn-secondary" @click="editingDesc = false">Cancel</button>
                <button class="btn-primary" @click="saveDesc">Save</button>
              </div>
            </div>
            <div v-else class="markdown-content" v-html="descriptionHtml" @click="startEditDesc"></div>
          </section>

          <section class="section">
            <h2 class="section-title">Documentation</h2>
            <div v-if="project.docs && project.docs.length > 0" class="docs-list">
              <div v-for="(doc, i) in project.docs" :key="i" class="doc-item">
                <McIcon name="external-link" :size="14" />
                <a :href="doc.url" target="_blank" rel="noopener">{{ doc.title }}</a>
                <button class="btn-ghost btn-sm" @click="removeDoc(i)">
                  <McIcon name="x" :size="12" />
                </button>
              </div>
            </div>
            <div v-else class="empty-section">No documentation links yet</div>
            <div class="add-doc-form">
              <input v-model="newDocTitle" class="mc-input" placeholder="Title (optional)" />
              <input v-model="newDocUrl" class="mc-input" placeholder="URL" />
              <button class="btn-primary btn-sm" @click="addDoc" :disabled="!newDocUrl">
                <McIcon name="plus" :size="14" />
                Add
              </button>
            </div>
          </section>
        </div>

        <!-- Tasks tab -->
        <div v-if="activeTab === 'tasks'" class="tab-content">
          <div v-if="!project.tasks || project.tasks.length === 0" class="empty-section">
            No tasks linked to this project
          </div>
          <div v-else>
            <div v-for="state in orderedStates" :key="state" class="task-group">
              <h3 class="group-title">{{ stateLabel(state) }} <span class="group-count">({{ tasksByState[state]?.length }})</span></h3>
              <div v-for="task in tasksByState[state]" :key="task.id" class="task-row">
                <span class="task-priority">{{ priorityLabel(task.priority) }}</span>
                <span class="task-title">{{ task.title }}</span>
                <span class="task-agent">{{ task.agent_id }}</span>
                <div class="task-tags">
                  <span v-for="tag in task.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Team tab -->
        <div v-if="activeTab === 'team'" class="tab-content">
          <div v-if="!project.agent_ids || project.agent_ids.length === 0" class="empty-section">
            No agents assigned to tasks in this project
          </div>
          <div v-else class="team-grid">
            <div v-for="agent in project.agent_ids" :key="agent" class="team-card">
              <McIcon name="bot" :size="24" />
              <span class="agent-name">{{ agent }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </PageShell>
</template>

<style scoped>
.detail-page {
  max-width: 1000px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: none;
  border: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
  margin-bottom: 1rem;
  transition: color var(--mc-transition-speed);
}
.back-btn:hover {
  color: var(--mc-accent);
}

.project-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.project-icon {
  font-size: 2.5rem;
}

.project-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--mc-text);
  margin: 0 0 0.25rem;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.meta-stat {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
}

.status-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-weight: 600;
  text-transform: uppercase;
}
.status-active { background: rgba(34,197,94,0.15); color: #22c55e; }
.status-paused { background: rgba(234,179,8,0.15); color: #eab308; }
.status-archived { background: rgba(107,114,128,0.15); color: #6b7280; }

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.75rem;
  background: var(--mc-accent);
  color: #fff;
  border: none;
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.75rem;
  background: var(--mc-bg-elevated);
  color: var(--mc-text);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-secondary:hover { border-color: var(--mc-accent); }

.btn-ghost {
  background: none;
  border: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--mc-radius-sm);
}
.btn-ghost:hover { color: var(--mc-accent); background: var(--mc-bg-elevated); }

.btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8rem; }

/* Tabs */
.tab-bar {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--mc-border);
  margin-bottom: 1.5rem;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.5rem 1rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--mc-text-muted);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--mc-transition-speed);
}
.tab-btn:hover { color: var(--mc-text); }
.tab-btn.active { color: var(--mc-accent); border-bottom-color: var(--mc-accent); }

.tab-content {
  animation: mc-fade-up 0.2s ease-out;
}

/* Sections */
.section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--mc-text);
  margin: 0;
}

.markdown-content {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  padding: 1rem;
  color: var(--mc-text);
  line-height: 1.6;
  cursor: pointer;
  font-size: 0.9rem;
}
.markdown-content:hover { border-color: var(--mc-accent); }

.mc-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: 0.85rem;
}
.mc-input:focus { border-color: var(--mc-accent); outline: none; }
.color-input { width: 60px; padding: 0.25rem; height: 36px; }

.mc-textarea {
  width: 100%;
  padding: 0.75rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-family: monospace;
  font-size: 0.85rem;
  resize: vertical;
}
.mc-textarea:focus { border-color: var(--mc-accent); outline: none; }

.form-row {
  margin-bottom: 0.75rem;
}
.form-row label {
  display: block;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.25rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.desc-editor {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  padding: 1rem;
}

/* Docs */
.docs-list {
  margin-bottom: 1rem;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--mc-border);
  font-size: 0.85rem;
}
.doc-item a {
  color: var(--mc-accent);
  text-decoration: none;
}
.doc-item a:hover { text-decoration: underline; }

.add-doc-form {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}
.add-doc-form .mc-input {
  flex: 1;
}

/* Tasks */
.task-group {
  margin-bottom: 1.5rem;
}

.group-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--mc-text);
  margin: 0 0 0.5rem;
  text-transform: capitalize;
}
.group-count {
  color: var(--mc-text-muted);
  font-weight: 400;
}

.task-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--mc-border);
  font-size: 0.85rem;
}

.task-priority { flex-shrink: 0; font-size: 0.8rem; }
.task-title { flex: 1; color: var(--mc-text); }
.task-agent { color: var(--mc-text-muted); font-size: 0.8rem; }

.task-tags {
  display: flex;
  gap: 0.25rem;
}
.tag {
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  background: var(--mc-bg-elevated);
  border-radius: 999px;
  color: var(--mc-text-muted);
}

/* Team */
.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.team-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
}

.agent-name {
  font-weight: 500;
  color: var(--mc-text);
}

/* Edit overlay */
.edit-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.edit-card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
}
.edit-card h3 {
  margin: 0 0 1rem;
  color: var(--mc-text);
}

.empty-section {
  padding: 1.5rem;
  text-align: center;
  color: var(--mc-text-muted);
  font-size: 0.85rem;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--mc-text-muted);
}
.error-state { color: #ef4444; }
</style>
