<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useMemoryStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'

const store = useMemoryStore()
const searchInput = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  store.fetchFiles()
})

watch(searchInput, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    store.search(val.trim())
  }, 300)
})

function highlightSnippet(snippet: string, query: string): string {
  if (!query) return escapeHtml(snippet)
  const escaped = escapeHtml(snippet)
  const escapedQuery = escapeHtml(query)
  const re = new RegExp(`(${escapedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return escaped.replace(re, '<mark>$1</mark>')
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(1)} KB`
}
</script>

<template>
  <PageShell>
    <div class="memory-page">
      <div class="memory-page__header">
        <h2 class="memory-page__title">Memory Explorer</h2>
        <p class="memory-page__subtitle">Browse and search Jeeves' memory system</p>
      </div>

      <!-- Search bar -->
      <div class="memory-page__search">
        <i class="pi pi-search memory-page__search-icon" />
        <input
          v-model="searchInput"
          type="text"
          class="memory-page__search-input"
          placeholder="Search memories... (min 2 characters)"
        />
        <span v-if="store.loading" class="memory-page__search-spinner">
          <i class="pi pi-spin pi-spinner" />
        </span>
      </div>

      <!-- Search results -->
      <div v-if="store.searchQuery && store.searchResults.length > 0" class="memory-page__results">
        <h3 class="memory-page__section-title">
          {{ store.searchResults.length }} result{{ store.searchResults.length !== 1 ? 's' : '' }}
          for "{{ store.searchQuery }}"
        </h3>
        <div class="memory-page__results-list mc-stagger">
          <RouterLink
            v-for="(hit, i) in store.searchResults"
            :key="i"
            :to="hit.date ? `/memory/daily/${hit.date}` : '/memory/long-term'"
            class="memory-page__hit"
          >
            <div class="memory-page__hit-meta">
              <span class="memory-page__hit-file mc-mono">{{ hit.filename }}</span>
              <span class="memory-page__hit-line mc-mono">L{{ hit.line_number }}</span>
            </div>
            <div
              v-if="hit.section_heading"
              class="memory-page__hit-section"
            >
              {{ hit.section_heading }}
            </div>
            <div
              class="memory-page__hit-snippet"
              v-html="highlightSnippet(hit.snippet, store.searchQuery)"
            />
          </RouterLink>
        </div>
      </div>

      <!-- No results -->
      <div v-else-if="store.searchQuery && store.searchResults.length === 0 && !store.loading" class="memory-page__empty">
        <p>No results for "{{ store.searchQuery }}"</p>
      </div>

      <!-- File browser (shown when not searching) -->
      <div v-if="!store.searchQuery">
        <!-- Long-term memory card -->
        <section class="memory-page__section">
          <h3 class="memory-page__section-title">Reference</h3>
          <RouterLink to="/memory/long-term" class="memory-page__card memory-page__card--accent">
            <div class="memory-page__card-icon"><McIcon name="brain" :size="22" /></div>
            <div class="memory-page__card-body">
              <span class="memory-page__card-title">MEMORY.md</span>
              <span class="memory-page__card-desc">Long-term memory — key context, people, preferences</span>
            </div>
            <i class="pi pi-chevron-right memory-page__card-arrow" />
          </RouterLink>
        </section>

        <!-- Daily logs -->
        <section class="memory-page__section">
          <h3 class="memory-page__section-title">
            Daily Logs
            <span class="memory-page__count">{{ store.files.length }}</span>
          </h3>
          <div v-if="store.files.length === 0 && !store.loading" class="memory-page__empty">
            <p>No daily memory files found.</p>
          </div>
          <div class="memory-page__files mc-stagger">
            <RouterLink
              v-for="file in store.files"
              :key="file.date"
              :to="`/memory/daily/${file.date}`"
              class="memory-page__card"
            >
              <div class="memory-page__card-date mc-mono">{{ file.date }}</div>
              <div class="memory-page__card-body">
                <span class="memory-page__card-preview">{{ file.preview }}</span>
                <div class="memory-page__card-meta">
                  <span>{{ file.section_count }} sections</span>
                  <span>{{ formatSize(file.size) }}</span>
                </div>
              </div>
              <i class="pi pi-chevron-right memory-page__card-arrow" />
            </RouterLink>
          </div>
        </section>
      </div>

      <!-- Error -->
      <div v-if="store.error" class="memory-page__error">
        <i class="pi pi-exclamation-triangle" />
        {{ store.error }}
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.memory-page {
  max-width: 960px;
}

.memory-page__header {
  margin-bottom: 1.5rem;
}

.memory-page__title {
  font-family: var(--mc-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.memory-page__subtitle {
  color: var(--mc-text-muted);
  font-size: 0.9rem;
}

/* Search */
.memory-page__search {
  position: relative;
  margin-bottom: 1.5rem;
}

.memory-page__search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--mc-text-muted);
  font-size: 0.9rem;
}

.memory-page__search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 2.5rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  font-family: var(--mc-font-body);
  font-size: 0.95rem;
  outline: none;
  transition: border-color var(--mc-transition-speed), box-shadow var(--mc-transition-speed);
}

.memory-page__search-input:focus {
  border-color: var(--mc-accent);
  box-shadow: 0 0 0 3px var(--mc-accent-subtle);
}

.memory-page__search-input::placeholder {
  color: var(--mc-text-muted);
}

.memory-page__search-spinner {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--mc-accent);
}

/* Sections */
.memory-page__section {
  margin-bottom: 2rem;
}

.memory-page__section-title {
  font-family: var(--mc-font-display);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mc-text-muted);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.memory-page__count {
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
  padding: 0.1rem 0.5rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-family: var(--mc-font-mono);
}

/* Cards */
.memory-page__files {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.memory-page__card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  text-decoration: none;
  color: var(--mc-text);
  transition: border-color var(--mc-transition-speed), background var(--mc-transition-speed), box-shadow var(--mc-transition-speed);
}

.memory-page__card:hover {
  border-color: var(--mc-border-strong);
  background: var(--mc-bg-elevated);
  box-shadow: var(--mc-shadow-sm);
}

.memory-page__card--accent {
  border-color: var(--mc-accent-subtle);
  background: linear-gradient(135deg, var(--mc-accent-subtle), transparent);
}

.memory-page__card--accent:hover {
  border-color: var(--mc-accent);
  box-shadow: var(--mc-shadow-glow);
}

.memory-page__card-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.memory-page__card-date {
  font-size: 0.85rem;
  color: var(--mc-accent);
  white-space: nowrap;
  flex-shrink: 0;
  font-weight: 500;
}

.memory-page__card-body {
  flex: 1;
  min-width: 0;
}

.memory-page__card-title {
  font-family: var(--mc-font-display);
  font-weight: 600;
  font-size: 1rem;
}

.memory-page__card-desc {
  color: var(--mc-text-muted);
  font-size: 0.85rem;
}

.memory-page__card-preview {
  display: block;
  color: var(--mc-text-muted);
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.memory-page__card-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  margin-top: 0.25rem;
}

.memory-page__card-arrow {
  color: var(--mc-text-muted);
  font-size: 0.8rem;
  flex-shrink: 0;
}

/* Search results */
.memory-page__results {
  margin-bottom: 2rem;
}

.memory-page__results-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.memory-page__hit {
  display: block;
  padding: 0.85rem 1rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  text-decoration: none;
  color: var(--mc-text);
  transition: border-color var(--mc-transition-speed), background var(--mc-transition-speed);
}

.memory-page__hit:hover {
  border-color: var(--mc-border-strong);
  background: var(--mc-bg-elevated);
}

.memory-page__hit-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  margin-bottom: 0.25rem;
}

.memory-page__hit-file {
  color: var(--mc-accent);
}

.memory-page__hit-section {
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: var(--mc-text);
}

.memory-page__hit-snippet {
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  line-height: 1.5;
}

.memory-page__hit-snippet :deep(mark) {
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
  padding: 0.1em 0.2em;
  border-radius: 2px;
}

/* Empty / Error */
.memory-page__empty {
  text-align: center;
  padding: 2rem;
  color: var(--mc-text-muted);
}

.memory-page__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-danger);
  font-size: 0.85rem;
  margin-top: 1rem;
}
</style>
