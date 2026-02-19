<template>
  <div class="content-pipeline">
    <div class="header">
      <div>
        <h1><i class="pi pi-video mr-2"></i>Content Pipeline</h1>
        <p class="subtitle">Idea to published content workflow</p>
      </div>
      <Button
        label="New Content"
        icon="pi pi-plus"
        @click="showCreateDialog = true"
        severity="success"
      />
    </div>

    <div v-if="error" class="error-banner">
      <i class="pi pi-exclamation-triangle mr-2"></i>
      {{ error }}
    </div>

    <!-- Stats -->
    <div class="stats-grid mb-4">
      <Card class="stat-card">
        <template #content>
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">Total Items</div>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
          <div class="stat-value">{{ stats.by_stage?.ideas || 0 }}</div>
          <div class="stat-label">In Ideas</div>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
          <div class="stat-value">{{ stats.by_stage?.filming || 0 }}</div>
          <div class="stat-label">Ready to Film</div>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
          <div class="stat-value">{{ stats.by_stage?.published || 0 }}</div>
          <div class="stat-label">Published</div>
        </template>
      </Card>
    </div>

    <!-- Kanban Board -->
    <div class="kanban-board">
      <div v-for="stage in stages" :key="stage.id" class="kanban-column">
        <div class="column-header" :style="{ borderTopColor: stage.color }">
          <div class="column-title">
            <i :class="stage.icon" class="mr-2"></i>
            {{ stage.name }}
          </div>
          <Badge :value="getStageItems(stage.id).length" />
        </div>
        <div class="column-content">
          <div v-if="getStageItems(stage.id).length === 0" class="empty-column">
            <i class="pi pi-inbox" style="font-size: 2rem; opacity: 0.3"></i>
            <p>No items</p>
          </div>
          <Card
            v-for="item in getStageItems(stage.id)"
            :key="item.id"
            class="content-card"
            @click="editItem(item)"
          >
            <template #title>
              <div class="card-title">
                {{ item.title }}
                <Tag
                  v-if="item.priority === 'high'"
                  value="High"
                  severity="danger"
                  size="small"
                />
              </div>
            </template>
            <template #subtitle>
              <Tag :value="item.type" severity="secondary" size="small" />
            </template>
            <template #content>
              <p v-if="item.description" class="card-description">
                {{ item.description }}
              </p>
              <div v-if="item.tags && item.tags.length > 0" class="card-tags">
                <Tag
                  v-for="tag in item.tags"
                  :key="tag"
                  :value="tag"
                  severity="secondary"
                  size="small"
                  class="mr-1"
                />
              </div>
              <div v-if="item.assigned_to" class="card-assignee">
                <i class="pi pi-user mr-1"></i>
                {{ item.assigned_to }}
              </div>
            </template>
            <template #footer>
              <div class="card-actions">
                <Button
                  v-if="stage.id !== 'published'"
                  label="Next Stage"
                  icon="pi pi-arrow-right"
                  size="small"
                  text
                  @click.stop="moveToNext(item, stage.id)"
                />
                <Button
                  icon="pi pi-trash"
                  size="small"
                  text
                  severity="danger"
                  @click.stop="confirmDelete(item)"
                />
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <Dialog
      v-model:visible="showCreateDialog"
      :header="editingItem ? 'Edit Content' : 'New Content'"
      modal
      :style="{ width: '500px' }"
    >
      <div class="dialog-content">
        <div class="field">
          <label for="title">Title</label>
          <InputText
            id="title"
            v-model="formData.title"
            placeholder="Content title"
            class="w-full"
          />
        </div>
        <div class="field">
          <label for="description">Description</label>
          <Textarea
            id="description"
            v-model="formData.description"
            placeholder="Brief description"
            rows="3"
            class="w-full"
          />
        </div>
        <div class="field">
          <label for="type">Type</label>
          <Dropdown
            id="type"
            v-model="formData.type"
            :options="contentTypes"
            optionLabel="label"
            optionValue="value"
            placeholder="Select type"
            class="w-full"
          />
        </div>
        <div class="field">
          <label for="priority">Priority</label>
          <Dropdown
            id="priority"
            v-model="formData.priority"
            :options="priorities"
            optionLabel="label"
            optionValue="value"
            placeholder="Select priority"
            class="w-full"
          />
        </div>
        <div class="field">
          <label for="tags">Tags (comma-separated)</label>
          <InputText
            id="tags"
            v-model="formData.tagsStr"
            placeholder="tag1, tag2, tag3"
            class="w-full"
          />
        </div>
        <div class="field">
          <label for="assigned_to">Assigned To</label>
          <Dropdown
            id="assigned_to"
            v-model="formData.assigned_to"
            :options="assigneeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select assignee"
            class="w-full"
          />
        </div>
        <div class="field" v-if="editingItem && editingItem.stage !== 'ideas'">
          <label for="script">Script</label>
          <Textarea
            id="script"
            v-model="formData.script"
            placeholder="Script content..."
            rows="4"
            class="w-full"
          />
        </div>
        <div class="field" v-if="editingItem && ['thumbnail', 'filming', 'editing', 'published'].includes(editingItem.stage)">
          <label for="thumbnail_url">Thumbnail URL</label>
          <InputText
            id="thumbnail_url"
            v-model="formData.thumbnail_url"
            placeholder="https://..."
            class="w-full"
          />
        </div>
        <div class="field" v-if="editingItem && ['editing', 'published'].includes(editingItem.stage)">
          <label for="video_url">Video URL</label>
          <InputText
            id="video_url"
            v-model="formData.video_url"
            placeholder="https://..."
            class="w-full"
          />
        </div>
        <div class="field" v-if="editingItem && editingItem.stage === 'published'">
          <label for="published_url">Published URL</label>
          <InputText
            id="published_url"
            v-model="formData.published_url"
            placeholder="https://..."
            class="w-full"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="showCreateDialog = false" />
        <Button
          :label="editingItem ? 'Update' : 'Create'"
          :loading="loading"
          @click="saveItem"
        />
      </template>
    </Dialog>

    <!-- Delete Confirmation -->
    <Dialog
      v-model:visible="showDeleteDialog"
      header="Confirm Delete"
      modal
      :style="{ width: '400px' }"
    >
      <p>Are you sure you want to delete "{{ itemToDelete?.title }}"?</p>
      <template #footer>
        <Button label="Cancel" text @click="showDeleteDialog = false" />
        <Button
          label="Delete"
          severity="danger"
          :loading="loading"
          @click="deleteItemConfirmed"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useContentStore } from './store'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Badge from 'primevue/badge'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import type { components } from '@/types/api'

type ContentItem = components['schemas']['ContentItem']

const store = useContentStore()

const loading = computed(() => store.loading)
const error = computed(() => store.error)
const stats = computed(() => store.stats)

const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const editingItem = ref<ContentItem | null>(null)
const itemToDelete = ref<ContentItem | null>(null)

const assigneeOptions = [
  { label: 'Unassigned', value: '' },
  { label: 'Human', value: 'human' },
  { label: 'Agent', value: 'agent' },
]

const formData = ref({
  title: '',
  description: '',
  type: 'video',
  priority: 'medium',
  tagsStr: '',
  assigned_to: '',
  script: '',
  thumbnail_url: '',
  video_url: '',
  published_url: '',
})

const stages = [
  { id: 'ideas', name: 'Ideas', icon: 'pi pi-lightbulb', color: '#fbbf24' },
  { id: 'scripting', name: 'Scripting', icon: 'pi pi-file-edit', color: '#3b82f6' },
  { id: 'thumbnail', name: 'Thumbnail', icon: 'pi pi-image', color: '#8b5cf6' },
  { id: 'filming', name: 'Filming', icon: 'pi pi-video', color: '#ec4899' },
  { id: 'editing', name: 'Editing', icon: 'pi pi-sliders-h', color: '#14b8a6' },
  { id: 'published', name: 'Published', icon: 'pi pi-check-circle', color: '#10b981' },
]

const contentTypes = [
  { label: 'Video', value: 'video' },
  { label: 'Article', value: 'article' },
  { label: 'Thread', value: 'thread' },
  { label: 'Tweet', value: 'tweet' },
  { label: 'Other', value: 'other' },
]

const priorities = [
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' },
]

onMounted(() => {
  store.fetchPipeline()
})

function getStageItems(stageId: string): ContentItem[] {
  return store.items.filter((item) => item.stage === stageId)
}

function editItem(item: ContentItem) {
  editingItem.value = item
  formData.value = {
    title: item.title,
    description: item.description || '',
    type: item.type,
    priority: item.priority,
    tagsStr: (item.tags || []).join(', '),
    assigned_to: item.assigned_to || '',
    script: item.script || '',
    thumbnail_url: item.thumbnail_url || '',
    video_url: item.video_url || '',
    published_url: item.published_url || '',
  }
  showCreateDialog.value = true
}

async function saveItem() {
  const tags = formData.value.tagsStr
    .split(',')
    .map((t) => t.trim())
    .filter((t) => t)

  if (editingItem.value) {
    await store.updateItem(editingItem.value.id, {
      title: formData.value.title,
      description: formData.value.description,
      type: formData.value.type as any,
      priority: formData.value.priority as any,
      tags,
      assigned_to: (formData.value.assigned_to || null) as any,
      script: formData.value.script || null,
      thumbnail_url: formData.value.thumbnail_url || null,
      video_url: formData.value.video_url || null,
      published_url: formData.value.published_url || null,
    })
  } else {
    await store.createItem({
      title: formData.value.title,
      description: formData.value.description,
      type: formData.value.type as any,
      priority: formData.value.priority as any,
      tags,
      stage: 'ideas',
    })
  }

  showCreateDialog.value = false
  editingItem.value = null
  resetForm()
}

function resetForm() {
  formData.value = {
    title: '',
    description: '',
    type: 'video',
    priority: 'medium',
    tagsStr: '',
    assigned_to: '',
    script: '',
    thumbnail_url: '',
    video_url: '',
    published_url: '',
  }
}

function confirmDelete(item: ContentItem) {
  itemToDelete.value = item
  showDeleteDialog.value = true
}

async function deleteItemConfirmed() {
  if (itemToDelete.value) {
    await store.deleteItem(itemToDelete.value.id)
    showDeleteDialog.value = false
    itemToDelete.value = null
  }
}

async function moveToNext(item: ContentItem, currentStage: string) {
  const currentIndex = stages.findIndex((s) => s.id === currentStage)
  if (currentIndex < stages.length - 1) {
    const nextStage = stages[currentIndex + 1].id
    await store.moveItem(item.id, nextStage)
  }
}
</script>

<style scoped>
.content-pipeline {
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
}

.subtitle {
  color: var(--text-color-secondary);
  margin: 0;
}

.error-banner {
  background: var(--red-100);
  color: var(--red-900);
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
  margin-top: 0.25rem;
}

/* Kanban Board */
.kanban-board {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  overflow-x: auto;
}

.kanban-column {
  background: var(--surface-50);
  border-radius: 8px;
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.column-header {
  padding: 1rem;
  border-top: 4px solid;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface-card);
}

.column-title {
  font-weight: 600;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
}

.column-content {
  padding: 1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-column {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-color-secondary);
}

.content-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.content-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.card-description {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
  margin: 0.5rem 0 0 0;
  line-height: 1.4;
}

.card-tags {
  margin-top: 0.5rem;
}

.card-assignee {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}

.card-actions {
  display: flex;
  justify-content: space-between;
}

/* Dialog */
.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  font-size: 0.9rem;
}
</style>
