<script setup lang="ts">
import { ref, watch } from 'vue'
import McIcon from '@/components/ui/McIcon.vue'
import { useProjectsStore } from '../store'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  created: []
}>()

const store = useProjectsStore()

const form = ref({
  id: '',
  name: '',
  icon: '📂',
  color: '',
  description: '',
  status: 'active',
})

const error = ref('')
const submitting = ref(false)

const colorOptions = [
  { label: 'None', value: '' },
  { label: 'Blue', value: '#3b82f6' },
  { label: 'Green', value: '#22c55e' },
  { label: 'Red', value: '#ef4444' },
  { label: 'Purple', value: '#a855f7' },
  { label: 'Orange', value: '#f97316' },
  { label: 'Pink', value: '#ec4899' },
  { label: 'Cyan', value: '#06b6d4' },
  { label: 'Yellow', value: '#eab308' },
]

function autoSlug() {
  if (!form.value.id || form.value.id === slugify(form.value.name.slice(0, -1))) {
    form.value.id = slugify(form.value.name)
  }
}

function slugify(text: string) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

async function submit() {
  error.value = ''
  if (!form.value.id || !form.value.name) {
    error.value = 'ID and Name are required'
    return
  }
  submitting.value = true
  try {
    await store.createProject(form.value)
    form.value = { id: '', name: '', icon: '📂', color: '', description: '', status: 'active' }
    emit('created')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to create project'
  } finally {
    submitting.value = false
  }
}

watch(() => props.visible, (v) => {
  if (v) {
    error.value = ''
    form.value = { id: '', name: '', icon: '📂', color: '', description: '', status: 'active' }
  }
})
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay" @click.self="emit('close')">
      <div class="dialog-card">
        <div class="dialog-header">
          <h2>New Project</h2>
          <button class="close-btn" @click="emit('close')">
            <McIcon name="x" :size="18" />
          </button>
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <div class="form-row">
          <label>Name</label>
          <input v-model="form.name" class="mc-input" placeholder="My Project" @input="autoSlug" />
        </div>

        <div class="form-row">
          <label>ID (slug)</label>
          <input v-model="form.id" class="mc-input" placeholder="my-project" />
        </div>

        <div class="form-row-inline">
          <div class="form-row">
            <label>Icon</label>
            <input v-model="form.icon" class="mc-input" placeholder="📂" />
          </div>
          <div class="form-row">
            <label>Color</label>
            <select v-model="form.color" class="mc-input">
              <option v-for="c in colorOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>Status</label>
            <select v-model="form.status" class="mc-input">
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <label>Description</label>
          <textarea v-model="form.description" class="mc-textarea" rows="3" placeholder="Project description…"></textarea>
        </div>

        <div class="dialog-actions">
          <button class="btn-secondary" @click="emit('close')">Cancel</button>
          <button class="btn-primary" @click="submit" :disabled="submitting">
            {{ submitting ? 'Creating…' : 'Create Project' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  padding: 1.5rem;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}
.dialog-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--mc-text);
}

.close-btn {
  background: none;
  border: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  padding: 0.25rem;
}
.close-btn:hover { color: var(--mc-text); }

.error-msg {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 0.5rem 0.75rem;
  border-radius: var(--mc-radius-sm);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.form-row {
  margin-bottom: 0.75rem;
  flex: 1;
}
.form-row label {
  display: block;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.25rem;
}

.form-row-inline {
  display: flex;
  gap: 0.75rem;
}

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

.mc-textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-size: 0.85rem;
  resize: vertical;
}
.mc-textarea:focus { border-color: var(--mc-accent); outline: none; }

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.5rem 1rem;
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
  padding: 0.5rem 1rem;
  background: var(--mc-bg-elevated);
  color: var(--mc-text);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-secondary:hover { border-color: var(--mc-accent); }
</style>
