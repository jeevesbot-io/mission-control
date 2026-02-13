<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAgentsStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'

const route = useRoute()
const store = useAgentsStore()
const statusFilter = ref<string>('')
const currentPage = ref(1)

const agentId = ref(route.params.agentId as string)

onMounted(() => {
  loadRuns()
})

watch(() => route.params.agentId, (newId) => {
  if (newId) {
    agentId.value = newId as string
    currentPage.value = 1
    statusFilter.value = ''
    loadRuns()
  }
})

function loadRuns() {
  store.fetchRuns(agentId.value, currentPage.value, statusFilter.value || undefined)
}

function setStatusFilter(status: string) {
  statusFilter.value = status
  currentPage.value = 1
  loadRuns()
}

function goPage(page: number) {
  currentPage.value = page
  loadRuns()
}

function statusClass(status: string): string {
  if (status === 'success') return 'detail__status--success'
  if (status === 'error' || status === 'failed') return 'detail__status--error'
  if (status === 'running' || status === 'pending') return 'detail__status--running'
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

function formatDuration(ms: number | null): string {
  if (ms === null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

async function handleTrigger() {
  const ok = await store.triggerAgent(agentId.value)
  if (ok) loadRuns()
}

const totalPages = () => Math.ceil(store.runsTotal / 20) || 1
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
        <div>
          <h2 class="detail__title mc-mono">{{ agentId }}</h2>
          <p class="detail__subtitle">{{ store.runsTotal }} total runs</p>
        </div>
        <button class="detail__trigger-btn" @click="handleTrigger">
          <i class="pi pi-play" /> Trigger Run
        </button>
      </div>

      <!-- Filters -->
      <div class="detail__filters">
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': statusFilter === '' }"
          @click="setStatusFilter('')"
        >All</button>
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': statusFilter === 'success' }"
          @click="setStatusFilter('success')"
        >Success</button>
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': statusFilter === 'error' }"
          @click="setStatusFilter('error')"
        >Error</button>
        <button
          class="detail__filter-btn"
          :class="{ 'detail__filter-btn--active': statusFilter === 'running' }"
          @click="setStatusFilter('running')"
        >Running</button>
      </div>

      <!-- Run History Table -->
      <div class="detail__table-wrap">
        <table class="detail__table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Type</th>
              <th>Trigger</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Tokens</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.runs.length === 0 && !store.loading">
              <td colspan="7" class="detail__empty">No runs found</td>
            </tr>
            <tr v-for="run in store.runs" :key="run.id">
              <td class="mc-mono">{{ formatDate(run.created_at) }}</td>
              <td>{{ run.run_type }}</td>
              <td>{{ run.trigger }}</td>
              <td>
                <span class="detail__status" :class="statusClass(run.status)">
                  {{ run.status }}
                </span>
              </td>
              <td class="mc-mono">{{ formatDuration(run.duration_ms) }}</td>
              <td class="mc-mono">{{ run.tokens_used ?? '—' }}</td>
              <td class="detail__summary">{{ run.summary ?? '—' }}</td>
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

.detail__title {
  font-family: var(--mc-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
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

/* Filters */
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

/* Table */
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

.detail__status {
  font-family: var(--mc-font-mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
}

.detail__status--success {
  color: var(--mc-success);
  background: color-mix(in srgb, var(--mc-success) 10%, transparent);
}

.detail__status--error {
  color: var(--mc-danger);
  background: color-mix(in srgb, var(--mc-danger) 10%, transparent);
}

.detail__status--running {
  color: var(--mc-live);
  background: color-mix(in srgb, var(--mc-live) 10%, transparent);
}

.detail__summary {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--mc-text-muted);
}

.detail__empty {
  text-align: center;
  color: var(--mc-text-muted);
  padding: 2rem;
}

/* Pagination */
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

/* Loading / Error */
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
