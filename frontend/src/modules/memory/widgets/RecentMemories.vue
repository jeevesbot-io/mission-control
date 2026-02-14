<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'

interface MemoryFileInfo {
  date: string
  filename: string
  size: number
  section_count: number
  preview: string
}

const api = useApi()
const files = ref<MemoryFileInfo[]>([])
const error = ref(false)

onMounted(async () => {
  try {
    const data = await api.get<{ files: MemoryFileInfo[] }>('/api/memory/files')
    files.value = data.files.slice(0, 3)
  } catch {
    error.value = true
  }
})
</script>

<template>
  <div class="recent-memories">
    <div class="recent-memories__header">
      <h3 class="recent-memories__title">Recent Memories</h3>
      <RouterLink to="/memory" class="recent-memories__link">View all</RouterLink>
    </div>

    <div v-if="error" class="recent-memories__error">
      <i class="pi pi-exclamation-triangle" />
      Memory module unavailable
    </div>

    <div v-else-if="files.length === 0" class="recent-memories__empty">
      No entries yet
    </div>

    <div v-else class="recent-memories__list">
      <RouterLink
        v-for="file in files"
        :key="file.date"
        :to="`/memory/daily/${file.date}`"
        class="recent-memories__item"
      >
        <span class="recent-memories__date mc-mono">{{ file.date }}</span>
        <span class="recent-memories__preview">{{ file.preview }}</span>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.recent-memories {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
}

.recent-memories__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.recent-memories__title {
  font-family: var(--mc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
}

.recent-memories__link {
  font-size: 0.75rem;
  color: var(--mc-accent);
  text-decoration: none;
}

.recent-memories__link:hover {
  color: var(--mc-accent-hover);
}

.recent-memories__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.recent-memories__item {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding: 0.5rem 0.6rem;
  border-radius: var(--mc-radius-sm);
  text-decoration: none;
  color: var(--mc-text);
  transition: background var(--mc-transition-speed);
}

.recent-memories__item:hover {
  background: var(--mc-bg-hover);
}

.recent-memories__date {
  font-size: 0.75rem;
  color: var(--mc-accent);
  white-space: nowrap;
  flex-shrink: 0;
}

.recent-memories__preview {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-memories__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-warning);
  padding: 0.5rem;
}

.recent-memories__empty {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  padding: 0.5rem;
}
</style>
