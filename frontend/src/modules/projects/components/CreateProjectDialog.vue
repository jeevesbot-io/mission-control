<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Button from 'primevue/button'
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

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Paused', value: 'paused' },
  { label: 'Archived', value: 'archived' },
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

function onHide() {
  emit('close')
}

watch(() => props.visible, (v) => {
  if (v) {
    error.value = ''
    form.value = { id: '', name: '', icon: '📂', color: '', description: '', status: 'active' }
  }
})
</script>

<template>
  <Dialog
    :visible="visible"
    header="New Project"
    :modal="true"
    :dismissableMask="true"
    :style="{ width: '500px' }"
    @update:visible="(val: boolean) => { if (!val) onHide() }"
  >
    <div v-if="error" class="error-msg">{{ error }}</div>

    <div class="field">
      <label>Name</label>
      <InputText v-model="form.name" placeholder="My Project" class="w-full" @input="autoSlug" />
    </div>

    <div class="field">
      <label>ID (slug)</label>
      <InputText v-model="form.id" placeholder="my-project" class="w-full" />
    </div>

    <div class="field-row">
      <div class="field">
        <label>Icon</label>
        <InputText v-model="form.icon" placeholder="📂" class="w-full" />
      </div>
      <div class="field">
        <label>Color</label>
        <Select
          v-model="form.color"
          :options="colorOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select color"
          class="w-full"
        />
      </div>
      <div class="field">
        <label>Status</label>
        <Select
          v-model="form.status"
          :options="statusOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select status"
          class="w-full"
        />
      </div>
    </div>

    <div class="field">
      <label>Description</label>
      <textarea v-model="form.description" class="mc-textarea" rows="3" placeholder="Project description…"></textarea>
    </div>

    <template #footer>
      <Button label="Cancel" severity="secondary" @click="onHide" />
      <Button :label="submitting ? 'Creating…' : 'Create Project'" @click="submit" :disabled="submitting" />
    </template>
  </Dialog>
</template>

<style scoped>
.error-msg {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 0.5rem 0.75rem;
  border-radius: var(--mc-radius-sm);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.field {
  margin-bottom: 0.75rem;
  flex: 1;
}
.field label {
  display: block;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.25rem;
}

.field-row {
  display: flex;
  gap: 0.75rem;
}

.w-full {
  width: 100%;
}

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
</style>
