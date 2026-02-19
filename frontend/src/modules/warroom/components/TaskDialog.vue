<template>
  <Dialog
    v-model:visible="visible"
    :header="isEdit ? 'Edit Task' : 'New Task'"
    :modal="true"
    :dismissableMask="true"
    class="task-dialog"
    :style="{ width: '540px' }"
  >
    <div class="dialog-body">
      <!-- Title -->
      <div class="field">
        <label>Title</label>
        <InputText v-model="form.title" placeholder="What needs to be done?" autofocus />
      </div>

      <!-- Description -->
      <div class="field">
        <label>Description</label>
        <Textarea v-model="form.description" placeholder="Optional details..." :rows="3" />
      </div>

      <!-- Priority + Status row -->
      <div class="field-row">
        <div class="field">
          <label>Priority</label>
          <div class="pill-row">
            <button
              v-for="p in priorities"
              :key="p.value"
              class="pill-btn"
              :class="{ active: form.priority === p.value, [`pill-${p.value}`]: true }"
              @click="form.priority = p.value"
            >{{ p.label }}</button>
          </div>
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

      <!-- Project + Skill row -->
      <div class="field-row">
        <div class="field">
          <label>Project</label>
          <Select
            v-model="form.project"
            :options="projectOptions"
            option-label="label"
            option-value="value"
            placeholder="None"
            class="w-full"
            show-clear
          />
        </div>
        <div class="field">
          <label>Skill</label>
          <InputText v-model="form.skill" placeholder="e.g. research" />
        </div>
      </div>

      <!-- Tags -->
      <div class="field">
        <label>Tags</label>
        <div class="tags-input">
          <span v-for="tag in form.tags" :key="tag" class="tag-chip">
            {{ tag }}
            <button class="tag-remove" @click="removeTag(tag)">×</button>
          </span>
          <input
            v-model="tagInput"
            class="tag-text-input"
            placeholder="Add tag, press Enter"
            @keydown.enter.prevent="addTag"
            @keydown.backspace="onTagBackspace"
          />
        </div>
      </div>

      <!-- Schedule -->
      <div class="field">
        <label>Schedule</label>
        <div class="pill-row">
          <button
            v-for="s in scheduleTypes"
            :key="s.value"
            class="pill-btn"
            :class="{ active: scheduleType === s.value }"
            @click="scheduleType = s.value"
          >{{ s.label }}</button>
        </div>
        <input
          v-if="scheduleType === 'specific'"
          v-model="specificTime"
          type="datetime-local"
          class="datetime-input"
        />
      </div>

      <!-- Estimated hours -->
      <div class="field">
        <label>Estimated hours <span class="label-muted">(optional)</span></label>
        <InputText v-model="estimatedHoursStr" type="number" min="0" step="0.5" placeholder="e.g. 2.5" />
      </div>

      <!-- References (edit mode only) -->
      <div v-if="isEdit" class="field">
        <label>References</label>
        <div class="refs-list">
          <div v-for="ref in form.references" :key="ref.id" class="ref-row">
            <span class="ref-type-icon">{{ refTypeIcon(ref.type) }}</span>
            <a :href="ref.url" target="_blank" class="ref-title">{{ ref.title }}</a>
            <button class="ref-delete" @click="$emit('delete-reference', ref.id)">×</button>
          </div>
        </div>
        <!-- Add reference form -->
        <div class="add-ref-form">
          <InputText v-model="refForm.title" placeholder="Title" />
          <InputText v-model="refForm.url" placeholder="URL or obsidian://..." />
          <button class="btn-secondary btn-sm" @click="submitRef">Add</button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <button v-if="isEdit" class="btn-danger" @click="$emit('delete', task?.id)">Delete</button>
          <button v-if="isEdit && task?.status !== 'done'" class="btn-run" @click="$emit('run', task!.id)">Run Now</button>
        </div>
        <div class="footer-right">
          <button class="btn-secondary" @click="visible = false">Cancel</button>
          <button class="btn-primary" :disabled="!form.title.trim()" @click="submit">
            {{ isEdit ? 'Save' : 'Create' }}
          </button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import { useWarRoomStore } from '../store'
import type { Task, Reference } from '../store'

const props = defineProps<{
  modelValue: boolean
  task?: Task | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'save', payload: Partial<Task>): void
  (e: 'delete', id: string | undefined): void
  (e: 'delete-reference', refId: string): void
  (e: 'add-reference', ref: Omit<Reference, 'id' | 'createdAt'>): void
  (e: 'run', id: string): void
}>()

const store = useWarRoomStore()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.task?.id)

const priorities = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
] as const

const statusOptions = [
  { value: 'backlog', label: 'Backlog' },
  { value: 'todo', label: 'Todo' },
  { value: 'in-progress', label: 'In Progress' },
  { value: 'done', label: 'Done' },
]

const scheduleTypes = [
  { value: 'none', label: 'None' },
  { value: 'asap', label: 'ASAP' },
  { value: 'next-heartbeat', label: 'Next Heartbeat' },
  { value: 'specific', label: 'Specific Time' },
]

const projectOptions = computed(() => [
  { value: null, label: 'No project' },
  ...store.activeProjectsWithCounts.map((p) => ({ value: p.id, label: p.name })),
])

// Form state
const defaultForm = () => ({
  title: '',
  description: '',
  priority: 'medium' as Task['priority'],
  status: 'backlog' as Task['status'],
  project: null as string | null,
  tags: [] as string[],
  skill: null as string | null,
  references: [] as Reference[],
  estimatedHours: null as number | null,
})

const form = ref(defaultForm())
const scheduleType = ref<'none' | 'asap' | 'next-heartbeat' | 'specific'>('none')
const specificTime = ref('')
const tagInput = ref('')
const estimatedHoursStr = ref('')

const refForm = ref({ title: '', url: '' })

// Populate form when task changes
watch(
  () => props.task,
  (task) => {
    if (task) {
      form.value = {
        title: task.title ?? '',
        description: task.description ?? '',
        priority: task.priority ?? 'medium',
        status: task.status ?? 'backlog',
        project: task.project ?? null,
        tags: [...(task.tags ?? [])],
        skill: task.skill ?? null,
        references: [...(task.references ?? [])],
        estimatedHours: task.estimatedHours ?? null,
      }
      estimatedHoursStr.value = task.estimatedHours != null ? String(task.estimatedHours) : ''
      const s = task.schedule
      if (!s) scheduleType.value = 'none'
      else if (s === 'asap') scheduleType.value = 'asap'
      else if (s === 'next-heartbeat') scheduleType.value = 'next-heartbeat'
      else { scheduleType.value = 'specific'; specificTime.value = s }
    } else {
      form.value = defaultForm()
      scheduleType.value = 'none'
      specificTime.value = ''
      estimatedHoursStr.value = ''
    }
    tagInput.value = ''
    refForm.value = { title: '', url: '' }
  },
  { immediate: true },
)

// Also sync references from the task prop (parent may update after ref deletion)
watch(
  () => props.task?.references,
  (refs) => {
    if (refs) form.value.references = [...refs]
  },
)

function addTag() {
  const t = tagInput.value.trim()
  if (t && !form.value.tags.includes(t)) form.value.tags.push(t)
  tagInput.value = ''
}

function removeTag(tag: string) {
  form.value.tags = form.value.tags.filter((t) => t !== tag)
}

function onTagBackspace() {
  if (!tagInput.value && form.value.tags.length) form.value.tags.pop()
}

function refTypeIcon(type: string): string {
  if (type === 'obsidian') return '🔮'
  if (type === 'doc') return '📄'
  return '🔗'
}

function submitRef() {
  if (!refForm.value.title.trim() || !refForm.value.url.trim()) return
  const type = refForm.value.url.startsWith('obsidian://')
    ? 'obsidian'
    : refForm.value.url.endsWith('.md')
    ? 'doc'
    : 'link'
  emit('add-reference', { title: refForm.value.title, url: refForm.value.url, type })
  refForm.value = { title: '', url: '' }
}

function submit() {
  if (!form.value.title.trim()) return
  const hours = estimatedHoursStr.value ? parseFloat(estimatedHoursStr.value) : null
  const schedule =
    scheduleType.value === 'none' ? null
    : scheduleType.value === 'specific' ? specificTime.value || null
    : scheduleType.value
  emit('save', {
    title: form.value.title.trim(),
    description: form.value.description,
    priority: form.value.priority,
    status: form.value.status,
    project: form.value.project || null,
    tags: form.value.tags,
    skill: form.value.skill || null,
    schedule,
    estimatedHours: isNaN(hours as number) ? null : hours,
  })
  visible.value = false
}
</script>

<style scoped>
.dialog-body { display: flex; flex-direction: column; gap: 1rem; padding-top: 0.25rem; }

.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field label { font-size: 0.75rem; font-weight: 600; color: var(--mc-text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.label-muted { text-transform: none; letter-spacing: 0; font-weight: 400; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }

.pill-row { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.pill-btn {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-family: var(--mc-font-mono);
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}
.pill-btn:hover { background: rgba(255,255,255,0.08); color: var(--mc-text); }
.pill-btn.active { border-color: var(--mc-accent); background: var(--mc-accent-subtle); color: var(--mc-accent); }
.pill-low.active    { border-color: rgba(107,112,132,0.5); background: rgba(107,112,132,0.12); color: var(--mc-text-muted); }
.pill-medium.active { border-color: rgba(96,165,250,0.5);  background: rgba(96,165,250,0.12);  color: #60a5fa; }
.pill-high.active   { border-color: rgba(251,191,36,0.5);  background: rgba(251,191,36,0.12);  color: #fbbf24; }
.pill-urgent.active { border-color: rgba(248,113,113,0.5); background: rgba(248,113,113,0.12); color: #f87171; }

.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  padding: 6px 8px;
  background: var(--mc-bg-elevated);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--mc-radius-sm);
  min-height: 38px;
  align-items: center;
}
.tag-chip {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.7rem;
  font-family: var(--mc-font-mono);
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
  border: 1px solid rgba(124,106,255,0.3);
  padding: 1px 6px;
  border-radius: 4px;
}
.tag-remove { background: none; border: none; cursor: pointer; color: var(--mc-accent); padding: 0; line-height: 1; font-size: 0.9rem; }
.tag-text-input {
  border: none;
  outline: none;
  background: transparent;
  color: var(--mc-text);
  font-size: 0.8rem;
  min-width: 100px;
  flex: 1;
}

.datetime-input {
  margin-top: 0.4rem;
  padding: 6px 10px;
  background: var(--mc-bg-elevated);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: 0.8rem;
  width: 100%;
  box-sizing: border-box;
}

.refs-list { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.5rem; }
.ref-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.78rem; }
.ref-type-icon { flex-shrink: 0; }
.ref-title { color: var(--mc-accent); text-decoration: none; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ref-title:hover { text-decoration: underline; }
.ref-delete { background: none; border: none; cursor: pointer; color: var(--mc-danger); font-size: 1rem; padding: 0 4px; line-height: 1; }

.add-ref-form { display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; }
.add-ref-form :deep(input) { flex: 1; min-width: 120px; }

.dialog-footer { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.footer-left { display: flex; gap: 0.5rem; }
.footer-right { display: flex; gap: 0.5rem; }

.btn-primary {
  padding: 6px 16px;
  border-radius: var(--mc-radius-sm);
  background: var(--mc-accent);
  color: #fff;
  font-weight: 600;
  font-size: 0.82rem;
  border: none;
  cursor: pointer;
  transition: opacity var(--mc-transition-speed);
}
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary:hover:not(:disabled) { opacity: 0.85; }

.btn-secondary {
  padding: 6px 16px;
  border-radius: var(--mc-radius-sm);
  background: rgba(255,255,255,0.06);
  color: var(--mc-text);
  font-size: 0.82rem;
  border: 1px solid rgba(255,255,255,0.1);
  cursor: pointer;
}
.btn-secondary:hover { background: rgba(255,255,255,0.1); }
.btn-sm { padding: 4px 10px; font-size: 0.75rem; }

.btn-danger {
  padding: 6px 14px;
  border-radius: var(--mc-radius-sm);
  background: rgba(248,113,113,0.12);
  color: #f87171;
  font-size: 0.82rem;
  border: 1px solid rgba(248,113,113,0.3);
  cursor: pointer;
}
.btn-danger:hover { background: rgba(248,113,113,0.2); }

.btn-run {
  padding: 6px 14px;
  border-radius: var(--mc-radius-sm);
  background: rgba(52,211,153,0.12);
  color: #34d399;
  font-size: 0.82rem;
  font-weight: 600;
  border: 1px solid rgba(52,211,153,0.3);
  cursor: pointer;
}
.btn-run:hover { background: rgba(52,211,153,0.2); }
</style>
