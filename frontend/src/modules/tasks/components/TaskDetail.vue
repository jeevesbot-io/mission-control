<template>
  <div class="task-detail">
    <!-- Header -->
    <div class="detail-header">
      <div class="detail-header__left">
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
      </div>
      <button class="detail-close" @click="emit('close')" title="Close (Esc)">
        <McIcon name="x" :size="18" />
      </button>
    </div>

    <!-- Body (scrollable) -->
    <div class="detail-body">
      <!-- Title -->
      <div class="detail-title-row">
        <input
          v-if="editingTitle"
          ref="titleInput"
          v-model="titleDraft"
          class="detail-title-input"
          @blur="saveTitle"
          @keydown.enter="saveTitle"
          @keydown.escape="cancelTitleEdit"
        />
        <h2 v-else class="detail-title" @click="startTitleEdit">{{ task.title }}</h2>
      </div>

      <!-- Status & Priority row -->
      <div class="detail-meta-row">
        <div class="detail-field">
          <label class="detail-label">Status</label>
          <select class="detail-select" :value="task.status" @change="onStatusChange">
            <option v-for="s in STATUS_ORDER" :key="s" :value="s">{{ STATUS_LABELS[s] }}</option>
          </select>
        </div>
        <div class="detail-field">
          <label class="detail-label">Priority</label>
          <select class="detail-select" :value="task.priority" @change="onPriorityChange">
            <option v-for="p in PRIORITY_ORDER" :key="p" :value="p">{{ PRIORITY_LABELS[p] }}</option>
          </select>
        </div>
      </div>

      <!-- Agent / Skill -->
      <div class="detail-field">
        <label class="detail-label">Agent</label>
        <select
          class="detail-select"
          :value="task.skill || ''"
          @change="onFieldChange('skill', ($event.target as HTMLSelectElement).value || null)"
        >
          <option value="">Unassigned</option>
          <option
            v-for="a in tasksStore.availableAgents"
            :key="a.agent_id"
            :value="a.agent_id"
          >
            {{ a.display_name }} ({{ a.role }})
          </option>
        </select>
      </div>

      <!-- Project -->
      <div class="detail-field">
        <label class="detail-label">Project</label>
        <select class="detail-select" :value="task.project || ''" @change="onProjectChange">
          <option value="">No project</option>
          <option v-for="p in tasksStore.projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>

      <!-- Tags -->
      <div class="detail-field">
        <label class="detail-label">Tags</label>
        <div class="tags-editor">
          <McChip
            v-for="tag in task.tags"
            :key="tag"
            mono
            size="sm"
            removable
            @remove="removeTag(tag)"
          >
            {{ tag }}
          </McChip>
          <input
            v-model="newTag"
            class="tag-input"
            placeholder="Add tag…"
            @keydown.enter.prevent="addTag"
          />
        </div>
      </div>

      <!-- Description -->
      <div class="detail-field">
        <div class="detail-label-row">
          <label class="detail-label">Description</label>
          <button class="edit-toggle" @click="editingDescription = !editingDescription">
            <McIcon :name="editingDescription ? 'eye' : 'pencil'" :size="13" />
          </button>
        </div>
        <textarea
          v-if="editingDescription"
          class="detail-textarea"
          :value="task.description"
          rows="6"
          placeholder="Add a description…"
          @change="onFieldChange('description', ($event.target as HTMLTextAreaElement).value)"
        />
        <div v-else class="detail-description mc-prose" v-html="renderedDescription" />
      </div>

      <!-- Blocked by -->
      <div v-if="task.blockedBy && task.blockedBy.length > 0" class="detail-field">
        <label class="detail-label">Blocked By</label>
        <div class="blockers-list">
          <div v-for="bid in task.blockedBy" :key="bid" class="blocker-item">
            <McIcon name="lock" :size="12" />
            <span>{{ getBlockerTitle(bid) }}</span>
          </div>
        </div>
      </div>

      <!-- References -->
      <div v-if="task.references && task.references.length > 0" class="detail-field">
        <label class="detail-label">References</label>
        <div class="refs-list">
          <a v-for="ref in task.references" :key="ref.id" :href="ref.url" target="_blank" class="ref-item">
            <McIcon name="external-link" :size="12" />
            {{ ref.title }}
          </a>
        </div>
      </div>

      <!-- Result / Error -->
      <div v-if="task.result || task.error" class="detail-field">
        <label class="detail-label">Result</label>
        <div v-if="task.error" class="result-error mc-mono">{{ task.error }}</div>
        <div v-else class="result-ok mc-mono">{{ task.result }}</div>
      </div>

      <!-- Comments -->
      <div class="detail-field">
        <label class="detail-label">Comments</label>
        <div class="placeholder-section">
          <McIcon name="message-square" :size="16" />
          <span>Comments coming soon</span>
        </div>
      </div>

      <!-- Activity -->
      <div class="detail-field">
        <label class="detail-label">Activity</label>
        <div class="placeholder-section">
          <McIcon name="activity" :size="16" />
          <span>Activity log coming soon</span>
        </div>
      </div>

      <!-- Timestamps -->
      <div class="detail-timestamps">
        <div class="timestamp-row">
          <span class="timestamp-label">Created</span>
          <span class="timestamp-value mc-mono">{{ formatDate(task.createdAt) }}</span>
        </div>
        <div class="timestamp-row">
          <span class="timestamp-label">Updated</span>
          <span class="timestamp-value mc-mono">{{ formatDate(task.updatedAt) }}</span>
        </div>
        <div v-if="task.completedAt" class="timestamp-row">
          <span class="timestamp-label">Completed</span>
          <span class="timestamp-value mc-mono">{{ formatDate(task.completedAt) }}</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="detail-footer">
      <McButton variant="danger" size="sm" icon="trash-2" @click="emit('delete', task.id)">
        Delete
      </McButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import McIcon from '@/components/ui/McIcon.vue'
import McChip from '@/components/ui/McChip.vue'
import McButton from '@/components/ui/McButton.vue'
import { useTasksStore } from '../store'
import type { Task, TaskStatus, TaskPriority } from '../store'
import { STATUS_ORDER, STATUS_LABELS, PRIORITY_ORDER, PRIORITY_LABELS } from '../store'

const props = defineProps<{ task: Task }>()
const emit = defineEmits<{
  close: []
  update: [id: string, payload: Partial<Task>]
  delete: [id: string]
}>()

const tasksStore = useTasksStore()

// Title editing
const editingTitle = ref(false)
const titleDraft = ref('')
const titleInput = ref<HTMLInputElement>()

function startTitleEdit() {
  titleDraft.value = props.task.title
  editingTitle.value = true
  nextTick(() => titleInput.value?.focus())
}

function saveTitle() {
  editingTitle.value = false
  const trimmed = titleDraft.value.trim()
  if (trimmed && trimmed !== props.task.title) {
    emit('update', props.task.id, { title: trimmed })
  }
}

function cancelTitleEdit() {
  editingTitle.value = false
}

// Description
const editingDescription = ref(false)

const renderedDescription = computed(() => {
  if (!props.task.description) return '<span class="no-desc">No description</span>'
  return DOMPurify.sanitize(marked.parse(props.task.description) as string)
})

// Status/Priority
function statusChipColor(status: TaskStatus): string {
  const map: Record<TaskStatus, string> = { backlog: 'blue', todo: 'blue', 'in-progress': 'amber', done: 'green' }
  return map[status] || 'blue'
}

function onStatusChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value as TaskStatus
  emit('update', props.task.id, { status: val })
}

function onPriorityChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value as TaskPriority
  emit('update', props.task.id, { priority: val })
}

function onProjectChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value || null
  emit('update', props.task.id, { project: val })
}

function onFieldChange(field: string, value: unknown) {
  emit('update', props.task.id, { [field]: value })
}

// Tags
const newTag = ref('')

function addTag() {
  const t = newTag.value.trim()
  if (t && !props.task.tags.includes(t)) {
    emit('update', props.task.id, { tags: [...props.task.tags, t] })
  }
  newTag.value = ''
}

function removeTag(tag: string) {
  emit('update', props.task.id, { tags: props.task.tags.filter((t) => t !== tag) })
}

// Helpers
function getBlockerTitle(id: string): string {
  const task = tasksStore.tasks.find((t) => t.id === id)
  return task ? task.title : id
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}
</script>

<style scoped>
.task-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--mc-bg-solid);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  flex-shrink: 0;
}

.detail-header__left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  border-radius: var(--mc-radius-xs);
  transition: all var(--mc-transition-speed);
}

.detail-close:hover {
  background: var(--mc-bg-hover);
  color: var(--mc-text);
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

/* Title */
.detail-title {
  font-family: var(--mc-font-display);
  font-size: var(--mc-text-xl);
  font-weight: 700;
  cursor: pointer;
  padding: 2px 4px;
  margin: 0;
  border-radius: var(--mc-radius-xs);
  transition: background var(--mc-transition-speed);
}

.detail-title:hover {
  background: var(--mc-bg-hover);
}

.detail-title-input {
  font-family: var(--mc-font-display);
  font-size: var(--mc-text-xl);
  font-weight: 700;
  width: 100%;
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-accent);
  border-radius: var(--mc-radius-xs);
  color: var(--mc-text);
  padding: 2px 4px;
  outline: none;
}

/* Fields */
.detail-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.detail-label {
  font-size: var(--mc-text-xs);
  font-weight: 600;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.detail-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.edit-toggle {
  background: none;
  border: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  padding: 2px;
  border-radius: var(--mc-radius-xs);
  transition: color var(--mc-transition-speed);
}

.edit-toggle:hover {
  color: var(--mc-accent);
}

.detail-meta-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.detail-select {
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border-input);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: var(--mc-text-sm);
  padding: 0.35rem 0.5rem;
  cursor: pointer;
  outline: none;
}

.detail-select:focus {
  border-color: var(--mc-accent);
}

.detail-select option {
  background: var(--mc-bg-elevated);
}

.detail-input {
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border-input);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: var(--mc-text-sm);
  padding: 0.35rem 0.5rem;
  outline: none;
}

.detail-input:focus {
  border-color: var(--mc-accent);
}

.detail-textarea {
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border-input);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: var(--mc-text-sm);
  font-family: var(--mc-font-mono);
  padding: 0.5rem;
  resize: vertical;
  outline: none;
}

.detail-textarea:focus {
  border-color: var(--mc-accent);
}

/* Description rendered */
.detail-description {
  font-size: var(--mc-text-sm);
  line-height: 1.6;
  min-height: 2em;
}

.detail-description :deep(.no-desc) {
  color: var(--mc-text-muted);
  font-style: italic;
}

/* Tags editor */
.tags-editor {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.tag-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--mc-text);
  font-size: var(--mc-text-xs);
  min-width: 80px;
  flex: 1;
}

/* Blockers */
.blockers-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.blocker-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: var(--mc-text-xs);
  color: var(--mc-danger);
}

/* References */
.refs-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.ref-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: var(--mc-text-xs);
  color: var(--mc-accent);
  text-decoration: none;
}

.ref-item:hover {
  text-decoration: underline;
}

/* Results */
.result-error {
  font-size: var(--mc-text-xs);
  color: var(--mc-danger);
  background: var(--mc-danger-bg);
  padding: 0.4rem 0.6rem;
  border-radius: var(--mc-radius-xs);
  border: 1px solid var(--mc-danger-border);
}

.result-ok {
  font-size: var(--mc-text-xs);
  color: var(--mc-success);
  background: var(--mc-success-bg);
  padding: 0.4rem 0.6rem;
  border-radius: var(--mc-radius-xs);
  border: 1px solid var(--mc-success-border);
}

/* Placeholder sections */
.placeholder-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--mc-bg-inset);
  border: 1px dashed var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text-muted);
  font-size: var(--mc-text-sm);
  font-style: italic;
}

/* Timestamps */
.detail-timestamps {
  border-top: 1px solid var(--mc-border);
  padding-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.timestamp-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timestamp-label {
  font-size: var(--mc-text-xs);
  color: var(--mc-text-muted);
}

.timestamp-value {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
}

/* Footer */
.detail-footer {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--mc-border);
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}
</style>
