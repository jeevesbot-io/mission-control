<template>
  <McModal
    :visible="true"
    header="New Task"
    width="480px"
    @update:visible="onVisibleChange"
  >
    <div class="create-form">
      <!-- Title -->
      <div class="field">
        <label class="field-label">Title</label>
        <input
          ref="titleInput"
          v-model="form.title"
          class="field-input"
          placeholder="What needs to be done?"
          @keydown.enter="submit"
          @keydown.escape="emit('close')"
        />
      </div>

      <!-- Status & Priority -->
      <div class="field-row">
        <div class="field">
          <label class="field-label">Status</label>
          <select v-model="form.status" class="field-select">
            <option v-for="s in STATUS_ORDER" :key="s" :value="s">{{ STATUS_LABELS[s] }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">Priority</label>
          <div class="priority-pills">
            <button
              v-for="p in PRIORITY_ORDER"
              :key="p"
              class="priority-pill"
              :class="{ active: form.priority === p }"
              :style="form.priority === p ? { borderColor: PRIORITY_COLORS[p], color: PRIORITY_COLORS[p] } : {}"
              @click="form.priority = p"
            >
              {{ PRIORITY_LABELS[p] }}
            </button>
          </div>
        </div>
      </div>

      <!-- Agent & Project -->
      <div class="field-row">
        <div class="field">
          <label class="field-label">Agent</label>
          <select v-model="form.skill" class="field-select">
            <option :value="null">Unassigned</option>
            <option
              v-for="a in tasksStore.availableAgents"
              :key="a.agent_id"
              :value="a.agent_id"
            >
              {{ a.agent_id }}
            </option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">Project</label>
          <select v-model="form.project" class="field-select">
            <option :value="null">No project</option>
            <option v-for="p in tasksStore.projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
      </div>

      <!-- Tags -->
      <div class="field">
        <label class="field-label">Tags</label>
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
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="modal-footer">
        <McButton variant="ghost" size="sm" @click="emit('close')">Cancel</McButton>
        <McButton variant="primary" size="sm" :disabled="!form.title.trim()" @click="submit">
          Create Task
        </McButton>
      </div>
    </template>
  </McModal>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import McModal from '@/components/ui/McModal.vue'
import McButton from '@/components/ui/McButton.vue'
import { useTasksStore } from '../store'
import type { TaskStatus, TaskPriority } from '../store'
import { STATUS_ORDER, STATUS_LABELS, PRIORITY_ORDER, PRIORITY_LABELS, PRIORITY_COLORS } from '../store'

const emit = defineEmits<{
  close: []
  created: []
}>()

const tasksStore = useTasksStore()
const titleInput = ref<HTMLInputElement>()
const tagInput = ref('')

const form = ref<{
  title: string
  status: TaskStatus
  priority: TaskPriority
  skill: string | null
  project: string | null
  tags: string[]
}>({
  title: '',
  status: 'todo',
  priority: 'medium',
  skill: null,
  project: null,
  tags: [],
})

function onVisibleChange(v: boolean) {
  if (!v) emit('close')
}

function addTag() {
  const t = tagInput.value.trim()
  if (t && !form.value.tags.includes(t)) {
    form.value.tags.push(t)
  }
  tagInput.value = ''
}

function removeTag(tag: string) {
  form.value.tags = form.value.tags.filter((t) => t !== tag)
}

async function submit() {
  if (!form.value.title.trim()) return
  await tasksStore.createTask({
    title: form.value.title.trim(),
    status: form.value.status,
    priority: form.value.priority,
    skill: form.value.skill,
    project: form.value.project,
    tags: form.value.tags,
  })
  emit('created')
}

onMounted(() => {
  nextTick(() => titleInput.value?.focus())
})
</script>

<style scoped>
.create-form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field-label {
  font-size: var(--mc-text-xs);
  font-weight: 600;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.field-input {
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border-input);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: var(--mc-text-sm);
  padding: 0.5rem 0.65rem;
  outline: none;
}

.field-input:focus {
  border-color: var(--mc-accent);
  box-shadow: 0 0 0 3px var(--mc-accent-glow);
}

.field-select {
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border-input);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: var(--mc-text-sm);
  padding: 0.4rem 0.5rem;
  cursor: pointer;
  outline: none;
}

.field-select option {
  background: var(--mc-bg-elevated);
}

.field-select:focus {
  border-color: var(--mc-accent);
}

/* Priority pills */
.priority-pills {
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.priority-pill {
  padding: 2px 8px;
  border-radius: var(--mc-radius-full);
  font-size: 0.65rem;
  font-family: var(--mc-font-mono);
  font-weight: 600;
  border: 1px solid var(--mc-border-input);
  background: var(--mc-bg-inset);
  color: var(--mc-text-muted);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}

.priority-pill:hover {
  background: var(--mc-bg-hover);
}

.priority-pill.active {
  background: var(--mc-accent-subtle);
}

/* Tags */
.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0.35rem 0.5rem;
  background: var(--mc-bg-inset);
  border: 1px solid var(--mc-border-input);
  border-radius: var(--mc-radius-sm);
  min-height: 34px;
  align-items: center;
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 0.65rem;
  font-family: var(--mc-font-mono);
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
  border: 1px solid var(--mc-accent-glow);
  padding: 0 5px;
  border-radius: 3px;
}

.tag-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mc-accent);
  padding: 0;
  line-height: 1;
  font-size: 0.85rem;
}

.tag-text-input {
  border: none;
  outline: none;
  background: transparent;
  color: var(--mc-text);
  font-size: var(--mc-text-xs);
  min-width: 80px;
  flex: 1;
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  width: 100%;
}
</style>
