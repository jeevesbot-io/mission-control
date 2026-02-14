<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAgentsStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'

const route = useRoute()
const store = useAgentsStore()
const levelFilter = ref<string>('')
const currentPage = ref(1)

const agentId = ref(route.params.agentId as string)

onMounted(() => {
  loadLog()
})

watch(() => route.params.agentId, (newId) => {
  if (newId) {
    agentId.value = newId as string
    currentPage.value = 1
    levelFilter.value = ''
    loadLog()
  }
})

function loadLog() {
  store.fetchLog(agentId.value, currentPage.value)
}

function setLevelFilter(level: string) {
  levelFilter.value = level
  currentPage.value = 1
  loadLog()
}

function goPage(page: number) {
  currentPage.value = page
  loadLog()
}

function levelClass(level: string): string {
  if (level === 'info') return 'detail__level--info'
  if (level === 'warning') return 'detail__level--warning'
  if (level === 'error') return 'detail__level--error'
  return ''
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatMetadata(meta: Record<string, unknown> | null): string {
  if (!meta) return '—'
  return Object.entries(meta)
    .map(([k, v]) => `${k}: ${v}`)
    .join(', ')
}

function agentIcon(id: string): string {
  const lower = id.toLowerCase()
  if (lower.includes('matron')) return '🏥'
  if (lower.includes('archivist')) return '📜'
  if (lower.includes('jeeves')) return '🫖'
  return '🤖'
}

async function handleTrigger() {
  const ok = await store.triggerAgent(agentId.value)
  if (ok) loadLog()
}

const totalPages = () => Math.ceil(store.logTotal / 20) || 1
</script>

<template>
  <PageShell>
    <div class="detail">
      <div class="detail__nav">
        <RouterLink to="/agents" class="detail__back">
          <i class="pi pi-arrow-left" /> All Agents
        </RouterLink>
      </div>

      <div class="detail__header">
        <div class="detail__header-left">
          <span class="detail__icon">{{ agentIcon(agentId) }}</span>
          <div>
            <h2 class="detail__title">{{ agentId }}</h2>
            <p class="detail__subtitle">{{ store.logTotal }} log entries</p>
          </div>
        </div>
        <button class="detail__trigger-btn" @click="handleTrigger">
          <i class="pi pi-play" /> Trigger
        </button>
      </div>

      <!-- Filters -->
      <div class="detail__filters">
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': levelFilter === '' }"
          @click="setLevelFilter('')"
        >All</button>
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': levelFilter === 'info' }"
          @click="setLevelFilter('info')"
        >Info</button>
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': levelFilter === 'warning' }"
          @click="setLevelFilter('warning')"
        >Warning</button>
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': levelFilter === 'error' }"
          @click="setLevelFilter('error')"
        >Error</button>
      </div>

      <!-- Log Table -->
      <div class="detail__table-wrap">
        <table class="detail__table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Level</th>
              <th>Message</th>
              <th>Metadata</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.logEntries.length === 0 && !store.loading">
              <td colspan="4" class="detail__empty">No log entries found</td>
            </tr>
            <tr v-for="entry in store.logEntries" :key="entry.id">
              <td class="mc-mono detail__time">{{ formatDate(entry.created_at) }}</td>
              <td>
                <span class="detail__level" :class="levelClass(entry.level)">
                  {{ entry.level }}
                </span>
              </td>
              <td class="detail__message">{{ entry.message }}</td>
              <td class="detail__meta mc-mono">{{ formatMetadata(entry.metadata) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages() > 1" class="detail__pagination">
        <button
          class="detail__page-btn"
          :disabled="currentPage <= 1"
          @click="goPage(currentPage - 1)"
        >
          <i class="pi pi-chevron-left" />
        </button>
        <span class="detail__page-info mc-mono">
          {{ currentPage }} / {{ totalPages() }}
        </span>
        <button
          class="detail__page-btn"
          :disabled="currentPage >= totalPages()"
          @click="goPage(currentPage + 1)"
        >
          <i class="pi pi-chevron-right" />
        </button>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" class="detail__loading">
        <i class="pi pi-spin pi-spinner" /> Loading...
      </div>

      <!-- Error -->
      <div v-if="store.error" class="detail__error">
        <i class="pi pi-exclamation-triangle" />
        {{ store.error }}
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.detail {
  max-width: 1100px;
}

.detail__nav {
  margin-bottom: 1rem;
}

.detail__back {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  text-decoration: none;
  transition: color var(--mc-transition-speed);
}

.detail__back:hover {
  color: var(--mc-accent);
}

.detail__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.detail__header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.detail__icon {
  font-size: 2rem;
}

.detail__title {
  font-family: var(--mc-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  text-transform: capitalize;
  margin-bottom: 0.1rem;
}

.detail__subtitle {
  color: var(--mc-text-muted);
  font-size: 0.85rem;
}

.detail__trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: var(--mc-accent);
  border: none;
  border-radius: var(--mc-radius-sm);
  color: white;
  font-family: var(--mc-font-body);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: opacity var(--mc-transition-speed);
}

.detail__trigger-btn:hover {
  opacity: 0.85;
}

.detail__filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.detail__filter-btn {
  padding: 0.35rem 0.75rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text-muted);
  font-family: var(--mc-font-body);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}

.detail__filter-btn:hover {
  border-color: var(--mc-border-strong);
  color: var(--mc-text);
}

.detail__filter-btn--active {
  background: var(--mc-accent-subtle);
  border-color: var(--mc-accent);
  color: var(--mc-accent);
}

.detail__table-wrap {
  overflow-x: auto;
  margin-bottom: 1rem;
}

.detail__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.detail__table th {
  text-align: left;
  padding: 0.6rem 0.75rem;
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mc-text-muted);
  border-bottom: 1px solid var(--mc-border);
}

.detail__table td {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--mc-border);
  color: var(--mc-text);
}

.detail__table tbody tr {
  transition: background var(--mc-transition-speed);
}

.detail__table tbody tr:hover {
  background: var(--mc-bg-surface);
}

.detail__time {
  white-space: nowrap;
  font-size: 0.75rem;
}

.detail__level {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
}

.detail__level--info {
  color: var(--mc-success);
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
}

.detail__level--warning {
  color: var(--mc-warning);
  background: color-mix(in srgb, var(--mc-warning) 10%, transparent);
}

.detail__level--error {
  color: var(--mc-danger);
  background: color-mix(in srgb, var(--mc-danger) 10%, transparent);
}

.detail__message {
  max-width: 400px;
}

.detail__meta {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}

.detail__empty {
  text-align: center;
  color: var(--mc-text-muted);
  padding: 2rem;
}

.detail__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.detail__page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text);
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}

.detail__page-btn:hover:not(:disabled) {
  border-color: var(--mc-accent);
  color: var(--mc-accent);
}

.detail__page-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.detail__page-info {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
}

.detail__loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--mc-text-muted);
  font-size: 0.85rem;
}

.detail__error {
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
