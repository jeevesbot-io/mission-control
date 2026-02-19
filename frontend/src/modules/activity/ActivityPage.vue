<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useActivityStore, type ActivityEvent } from './store'
import { useWebSocket } from '@/composables/useWebSocket'
import PageShell from '@/components/layout/PageShell.vue'
import StatCard from '@/components/data/StatCard.vue'
import McIcon from '@/components/ui/McIcon.vue'

const store = useActivityStore()
const { subscribe } = useWebSocket()

const moduleFilter = ref('')
const actorFilter = ref('')

const modules = [
  { label: 'All', value: '' },
  { label: 'War Room', value: 'warroom' },
  { label: 'Agents', value: 'agents' },
  { label: 'Content', value: 'content' },
]

let unsubscribe: (() => void) | undefined

onMounted(() => {
  loadFeed()
  store.fetchStats()

  unsubscribe = subscribe('activity:new', (data) => {
    store.prependEvent(data as unknown as ActivityEvent)
  })
})

onUnmounted(() => {
  if (unsubscribe) unsubscribe()
})

function loadFeed() {
  store.fetchFeed(50, {
    module: moduleFilter.value || undefined,
    actor: actorFilter.value || undefined,
  })
}

function handleLoadMore() {
  store.loadMore(50, {
    module: moduleFilter.value || undefined,
    actor: actorFilter.value || undefined,
  })
}

function setModuleFilter(value: string) {
  moduleFilter.value = value
  loadFeed()
}

function iconForResource(type: string): string {
  const map: Record<string, string> = {
    task: 'kanban',
    agent: 'bot',
    model: 'cpu',
    skill: 'sparkles',
    soul: 'file-text',
    content: 'video',
  }
  return map[type] || 'activity'
}

function accentForModule(mod: string): string {
  const map: Record<string, string> = {
    warroom: 'var(--mc-warning)',
    agents: '#7c6aff',
    content: '#ec4899',
  }
  return map[mod] || 'var(--mc-accent)'
}

function actionLabel(action: string): string {
  const parts = action.split('.')
  if (parts.length === 2) {
    return `${parts[0]} ${parts[1]}`
  }
  return action.replace(/\./g, ' ')
}

function formatRelative(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = now - then
  const secs = Math.round(diff / 1000)
  if (secs < 60) return 'just now'
  const mins = Math.round(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}

function resourceLink(event: ActivityEvent): string | null {
  if (event.resource_type === 'agent' && event.resource_id) {
    return `/agents/${event.resource_id}`
  }
  if (event.module === 'warroom' && event.resource_type === 'task') {
    return '/warroom'
  }
  if (event.module === 'content') {
    return '/content'
  }
  return null
}
</script>

<template>
  <PageShell>
    <div class="activity">
      <div class="activity__header">
        <h2 class="activity__title">Activity Timeline</h2>
        <p class="activity__subtitle">Cross-module event feed</p>
      </div>

      <!-- Stats -->
      <section class="activity__section" v-if="store.stats">
        <h3 class="activity__section-title">Overview</h3>
        <div class="activity__stats mc-stagger">
          <StatCard icon="activity" accent="#7c6aff" :value="store.stats.total_events" label="Total Events" />
          <StatCard icon="clock" accent="#38bdf8" :value="store.stats.last_24h" label="Last 24h" />
          <StatCard icon="swords" accent="var(--mc-warning)" :value="store.stats.by_module?.warroom || 0" label="War Room" />
          <StatCard icon="bot" accent="#a78bfa" :value="store.stats.by_module?.agents || 0" label="Agents" />
          <StatCard icon="video" accent="#ec4899" :value="store.stats.by_module?.content || 0" label="Content" />
        </div>
      </section>

      <!-- Filters -->
      <div class="activity__filters">
        <button
          v-for="m in modules"
          :key="m.value"
          class="activity__filter-btn"
          :class="{ 'activity__filter-btn--active': moduleFilter === m.value }"
          @click="setModuleFilter(m.value)"
        >{{ m.label }}</button>
      </div>

      <!-- Timeline -->
      <div class="activity__timeline">
        <div v-if="store.events.length === 0 && !store.loading" class="activity__empty">
          <McIcon name="activity" :size="32" class="activity__empty-icon" />
          <span>No activity recorded yet</span>
        </div>

        <div
          v-for="event in store.events"
          :key="event.id"
          class="activity__event"
        >
          <div class="activity__event-line">
            <div
              class="activity__event-dot"
              :style="{ background: accentForModule(event.module) }"
            />
          </div>
          <div class="activity__event-content">
            <div class="activity__event-top">
              <McIcon :name="iconForResource(event.resource_type)" :size="16" class="activity__event-icon" />
              <span class="activity__event-action">{{ actionLabel(event.action) }}</span>
              <span class="activity__event-module mc-mono">{{ event.module }}</span>
            </div>
            <div class="activity__event-detail">
              <span v-if="event.resource_name" class="activity__event-resource">{{ event.resource_name }}</span>
              <span class="activity__event-actor mc-mono">by {{ event.actor }}</span>
            </div>
            <div class="activity__event-bottom">
              <span class="activity__event-time mc-mono">{{ formatRelative(event.timestamp) }}</span>
              <RouterLink
                v-if="resourceLink(event)"
                :to="resourceLink(event)!"
                class="activity__event-link"
              >View</RouterLink>
            </div>
          </div>
        </div>
      </div>

      <!-- Load More -->
      <div v-if="store.cursor && store.events.length > 0" class="activity__load-more">
        <button
          class="activity__load-btn"
          :disabled="store.loading"
          @click="handleLoadMore"
        >
          <template v-if="store.loading">Loading...</template>
          <template v-else>Load more</template>
        </button>
      </div>

      <!-- Loading -->
      <div v-if="store.loading && store.events.length === 0" class="activity__loading">
        <i class="pi pi-spin pi-spinner" /> Loading...
      </div>

      <!-- Error -->
      <div v-if="store.error" class="activity__error">
        <i class="pi pi-exclamation-triangle" />
        {{ store.error }}
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.activity {
  max-width: 800px;
}

.activity__header {
  margin-bottom: 1.5rem;
}

.activity__title {
  font-family: var(--mc-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.activity__subtitle {
  color: var(--mc-text-muted);
  font-size: 0.9rem;
}

.activity__section {
  margin-bottom: 2rem;
}

.activity__section-title {
  font-family: var(--mc-font-display);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mc-text-muted);
  margin-bottom: 0.75rem;
}

.activity__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

.activity__filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.activity__filter-btn {
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

.activity__filter-btn:hover {
  border-color: var(--mc-border-strong);
  color: var(--mc-text);
}

.activity__filter-btn--active {
  background: var(--mc-accent-subtle);
  border-color: var(--mc-accent);
  color: var(--mc-accent);
}

/* Timeline */
.activity__timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.activity__event {
  display: flex;
  gap: 1rem;
  padding: 0.75rem 0;
  transition: background var(--mc-transition-speed);
}

.activity__event:hover {
  background: var(--mc-bg-surface);
  border-radius: var(--mc-radius-sm);
}

.activity__event-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
  position: relative;
}

.activity__event-line::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  background: var(--mc-border);
  transform: translateX(-50%);
}

.activity__event-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  z-index: 1;
  margin-top: 0.35rem;
}

.activity__event-content {
  flex: 1;
  min-width: 0;
}

.activity__event-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.2rem;
}

.activity__event-icon {
  flex-shrink: 0;
  color: var(--mc-text-muted);
}

.activity__event-action {
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: capitalize;
}

.activity__event-module {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
}

.activity__event-detail {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.2rem;
}

.activity__event-resource {
  font-size: 0.8rem;
  color: var(--mc-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity__event-actor {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
  flex-shrink: 0;
}

.activity__event-bottom {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.activity__event-time {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
}

.activity__event-link {
  font-size: 0.7rem;
  color: var(--mc-accent);
  text-decoration: none;
}

.activity__event-link:hover {
  text-decoration: underline;
}

/* Load more */
.activity__load-more {
  display: flex;
  justify-content: center;
  padding: 1rem 0;
}

.activity__load-btn {
  padding: 0.5rem 1.25rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text-muted);
  font-family: var(--mc-font-body);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--mc-transition-speed);
}

.activity__load-btn:hover:not(:disabled) {
  border-color: var(--mc-accent);
  color: var(--mc-accent);
}

.activity__load-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty / Loading / Error */
.activity__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 3rem;
  color: var(--mc-text-muted);
  font-size: 0.9rem;
}

.activity__empty-icon {
  opacity: 0.5;
}

.activity__loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--mc-text-muted);
  font-size: 0.85rem;
  margin-top: 1rem;
}

.activity__error {
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
