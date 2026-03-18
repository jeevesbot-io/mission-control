<template>
  <PageShell>
    <div class="skills-page">
      <!-- Header -->
      <div class="skills-header">
        <div class="header-left">
          <h1 class="page-title">
            <McIcon name="sparkles" :size="24" />
            Skills Browser
            <span v-if="!loading" class="count-badge">{{ filteredSkills.length }}</span>
          </h1>
        </div>
        <div class="header-right">
          <button
            class="reindex-btn"
            :disabled="reindexing"
            @click="handleReindex"
          >
            <McIcon :name="reindexing ? 'loader' : 'refresh-cw'" :size="16" />
            {{ reindexing ? 'Indexing...' : 'Re-index' }}
          </button>
        </div>
      </div>

      <!-- Toast notification -->
      <Transition name="toast">
        <div v-if="toastVisible" class="toast" :class="toastType">
          {{ toastMessage }}
        </div>
      </Transition>

      <!-- Stats bar -->
      <div class="stats-bar" v-if="skills.length">
        <div class="stat">
          <span class="stat-value">{{ skills.length }}</span>
          <span class="stat-label">Total</span>
        </div>
        <div class="stat">
          <span class="stat-value source-system-text">{{ sourceCounts.System }}</span>
          <span class="stat-label">System</span>
        </div>
        <div class="stat">
          <span class="stat-value source-user-text">{{ sourceCounts.User }}</span>
          <span class="stat-label">User</span>
        </div>
        <div class="stat">
          <span class="stat-value source-workspace-text">{{ sourceCounts.Workspace }}</span>
          <span class="stat-label">Workspace</span>
        </div>
        <div class="stat">
          <span class="stat-value source-extension-text">{{ sourceCounts.Extension }}</span>
          <span class="stat-label">Extension</span>
        </div>
        <div v-if="driftCount > 0" class="stat">
          <span class="stat-value drift-text">{{ driftCount }}</span>
          <span class="stat-label">Drifted</span>
        </div>
      </div>

      <!-- Filters -->
      <div class="filters-row">
        <InputText
          v-model="search"
          placeholder="Search skills..."
          class="search-input"
        />
        <div class="source-filters">
          <button
            v-for="f in sourceFilters"
            :key="f.value"
            class="filter-btn"
            :class="{ active: activeSource === f.value }"
            @click="activeSource = f.value"
          >
            {{ f.label }}
          </button>
          <button
            class="filter-btn drift-filter"
            :class="{ active: showDriftedOnly }"
            @click="showDriftedOnly = !showDriftedOnly"
          >
            ⚠️ Drifted
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <McIcon name="loader" :size="20" />
        Loading skills...
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredSkills.length === 0" class="empty-state">
        <McIcon name="search-x" :size="32" />
        <p>No skills found{{ search ? ' matching your search' : '' }}</p>
      </div>

      <!-- Skills grid -->
      <div v-else class="skills-grid">
        <div
          v-for="skill in filteredSkills"
          :key="skill.name"
          class="skill-card"
          @click="openSkill(skill)"
        >
          <div class="card-header">
            <div class="card-header-left">
              <span class="skill-name">{{ skill.name }}</span>
              <span
                v-if="skill.has_drift"
                class="drift-badge"
                title="Drift detected — files changed since last index"
              >⚠️</span>
            </div>
            <span class="source-badge" :class="`source-${(skill.source_label || skill.source || '').toLowerCase()}`">
              {{ skill.source_label || skill.source }}
            </span>
          </div>
          <p class="skill-description">{{ skill.description || 'No description' }}</p>
          <div v-if="skill.file_count != null" class="card-meta">
            <span class="meta-item">{{ skill.file_count }} files</span>
          </div>
        </div>
      </div>

      <!-- Detail drawer -->
      <Dialog
        v-model:visible="drawerVisible"
        :header="selectedName"
        position="right"
        :modal="true"
        :dismissableMask="true"
        class="skill-drawer"
        :style="{ width: '600px', height: '100vh', margin: 0, borderRadius: 0 }"
      >
        <div class="markdown-body" v-html="renderedMarkdown"></div>
      </Dialog>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import { useSkillsStore, type SkillInfo } from './store'
import { storeToRefs } from 'pinia'

const store = useSkillsStore()
const { skills, loading, reindexing, selectedContent, selectedName } = storeToRefs(store)

const search = ref('')
const activeSource = ref<string>('all')
const showDriftedOnly = ref(false)
const drawerVisible = ref(false)
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')

const sourceFilters = [
  { label: 'All', value: 'all' },
  { label: 'System', value: 'System' },
  { label: 'User', value: 'User' },
  { label: 'Workspace', value: 'Workspace' },
  { label: 'Extension', value: 'Extension' },
]

const sourceCounts = computed(() => {
  const counts: Record<string, number> = { System: 0, User: 0, Workspace: 0, Extension: 0 }
  for (const s of skills.value) {
    const label = s.source_label ?? s.source ?? ''
    if (label in counts) counts[label] = (counts[label] ?? 0) + 1
  }
  return counts
})

const driftCount = computed(() => skills.value.filter(s => s.has_drift).length)

const filteredSkills = computed(() => {
  let result = skills.value
  if (activeSource.value !== 'all') {
    result = result.filter(s => (s.source_label ?? s.source) === activeSource.value)
  }
  if (showDriftedOnly.value) {
    result = result.filter(s => s.has_drift)
  }
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter(
      s => s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q)
    )
  }
  return result
})

const renderedMarkdown = computed(() => {
  if (!selectedContent.value) return ''
  return DOMPurify.sanitize(marked(selectedContent.value) as string)
})

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toastMessage.value = msg
  toastType.value = type
  toastVisible.value = true
  setTimeout(() => { toastVisible.value = false }, 4000)
}

async function handleReindex() {
  try {
    const result = await store.reindex()
    showToast(
      `Indexed ${result.indexed} skills in ${result.duration_ms}ms — ${result.new} new, ${result.drifted} drifted, ${result.removed} removed`,
      'success'
    )
  } catch (e) {
    showToast('Re-index failed: ' + (e instanceof Error ? e.message : 'Unknown error'), 'error')
  }
}

async function openSkill(skill: SkillInfo) {
  drawerVisible.value = true
  await store.fetchSkillContent(skill.name)
}

onMounted(() => {
  store.fetchSkills()
})
</script>

<style scoped>
.skills-page {
  max-width: 1200px;
  margin: 0 auto;
}

.skills-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--mc-text);
  margin: 0;
}

.count-badge {
  font-size: 0.85rem;
  font-weight: 500;
  background: var(--mc-bg-elevated);
  color: var(--mc-text-muted);
  padding: 0.15rem 0.5rem;
  border-radius: var(--mc-radius-sm);
}

.reindex-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-bg-surface);
  color: var(--mc-text);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.15s;
}

.reindex-btn:hover:not(:disabled) {
  border-color: var(--mc-accent);
  color: var(--mc-accent);
}

.reindex-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Toast */
.toast {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  padding: 0.75rem 1.25rem;
  border-radius: var(--mc-radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toast.success {
  background: #065f46;
  color: #d1fae5;
  border: 1px solid #10b981;
}

.toast.error {
  background: #7f1d1d;
  color: #fecaca;
  border: 1px solid #ef4444;
}

.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Stats bar */
.stats-bar {
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem 1rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  margin-bottom: 1rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--mc-text);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.source-system-text    { color: #60a5fa; }
.source-user-text      { color: #34d399; }
.source-workspace-text { color: #a78bfa; }
.source-extension-text { color: #fb923c; }
.drift-text            { color: #fbbf24; }

/* Filters */
.filters-row {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.source-filters {
  display: flex;
  gap: 0.25rem;
}

.filter-btn {
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-bg-surface);
  color: var(--mc-text-muted);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--mc-transition-speed, 0.15s);
}

.filter-btn:hover {
  border-color: var(--mc-accent);
  color: var(--mc-text);
}

.filter-btn.active {
  background: var(--mc-accent);
  color: #fff;
  border-color: var(--mc-accent);
}

.drift-filter.active {
  background: #92400e;
  border-color: #fbbf24;
  color: #fbbf24;
}

/* Grid */
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.skill-card {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  padding: 1rem;
  cursor: pointer;
  transition: all var(--mc-transition-speed, 0.15s);
}

.skill-card:hover {
  border-color: var(--mc-accent);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.skill-name {
  font-weight: 600;
  color: var(--mc-text);
  font-size: 0.95rem;
}

.drift-badge {
  font-size: 0.8rem;
  cursor: help;
}

.source-badge {
  font-size: 0.7rem;
  font-weight: 500;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.source-system    { background: rgba(96,165,250,0.15);  color: #60a5fa; }
.source-user      { background: rgba(52,211,153,0.15);  color: #34d399; }
.source-workspace { background: rgba(167,139,250,0.15); color: #a78bfa; }
.source-extension { background: rgba(251,146,60,0.15);  color: #fb923c; }

.skill-description {
  color: var(--mc-text-muted);
  font-size: 0.85rem;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.75rem;
}

.meta-item {
  font-size: 0.75rem;
  color: var(--mc-text-muted);
}

/* Loading / empty states */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem;
  color: var(--mc-text-muted);
}

/* Markdown body in drawer */
:deep(.markdown-body) {
  color: var(--mc-text);
  line-height: 1.6;
  font-size: 0.9rem;
}

:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3),
:deep(.markdown-body h4) {
  color: var(--mc-text);
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

:deep(.markdown-body h1) { font-size: 1.4rem; }
:deep(.markdown-body h2) { font-size: 1.2rem; }
:deep(.markdown-body h3) { font-size: 1.05rem; }

:deep(.markdown-body p) {
  margin: 0.5rem 0;
}

:deep(.markdown-body code) {
  background: var(--mc-bg-elevated);
  padding: 0.15rem 0.35rem;
  border-radius: 3px;
  font-size: 0.85em;
}

:deep(.markdown-body pre) {
  background: var(--mc-bg-elevated);
  padding: 1rem;
  border-radius: var(--mc-radius-sm);
  overflow-x: auto;
  margin: 0.75rem 0;
}

:deep(.markdown-body pre code) {
  background: none;
  padding: 0;
}

:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  padding-left: 1.5rem;
  margin: 0.5rem 0;
}

:deep(.markdown-body li) {
  margin: 0.25rem 0;
}

:deep(.markdown-body a) {
  color: var(--mc-accent);
  text-decoration: none;
}

:deep(.markdown-body a:hover) {
  text-decoration: underline;
}

:deep(.markdown-body blockquote) {
  border-left: 3px solid var(--mc-border);
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: var(--mc-text-muted);
}

:deep(.markdown-body hr) {
  border: none;
  border-top: 1px solid var(--mc-border);
  margin: 1rem 0;
}

:deep(.markdown-body table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75rem 0;
}

:deep(.markdown-body th),
:deep(.markdown-body td) {
  border: 1px solid var(--mc-border);
  padding: 0.5rem;
  text-align: left;
}

:deep(.markdown-body th) {
  background: var(--mc-bg-elevated);
  font-weight: 600;
}
</style>

<style>
/* Dialog positioning overrides (unscoped so they apply to PrimeVue portal) */
.skill-drawer.p-dialog {
  max-height: 100vh !important;
}

.skill-drawer .p-dialog-content {
  overflow-y: auto;
  flex: 1;
}
</style>
