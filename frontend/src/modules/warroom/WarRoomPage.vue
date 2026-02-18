<template>
  <PageShell>
    <div class="warroom-page">
      <!-- Tab bar -->
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="switchTab(tab.id)"
        >
          <McIcon :name="tab.icon" :size="14" />
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab content -->
      <div class="tab-content">
        <!-- Kanban -->
        <TaskBoard v-if="activeTab === 'kanban'" />

        <!-- Usage & Model -->
        <div v-else-if="activeTab === 'usage'" class="tab-panel">
          <h2 class="section-title">Usage & Model</h2>
          <UsagePanel />
        </div>

        <!-- Skills -->
        <div v-else-if="activeTab === 'skills'" class="tab-panel">
          <h2 class="section-title">Skills</h2>
          <SkillsList v-if="visitedTabs.has('skills')" />
          <div v-else class="loading-placeholder">Loading…</div>
        </div>

        <!-- Soul & Identity -->
        <div v-else-if="activeTab === 'soul'" class="tab-panel">
          <h2 class="section-title">Soul & Identity</h2>
          <SoulEditor v-if="visitedTabs.has('soul')" />
          <div v-else class="loading-placeholder">Loading…</div>
        </div>

        <!-- Calendar -->
        <div v-else-if="activeTab === 'calendar'" class="tab-panel">
          <h2 class="section-title">Activity Calendar</h2>
          <ActivityCalendar v-if="visitedTabs.has('calendar')" />
          <div v-else class="loading-placeholder">Loading…</div>
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { defineAsyncComponent, onMounted, ref } from 'vue'
import { useWarRoomStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'
import McIcon from '@/components/ui/McIcon.vue'
import TaskBoard from './components/TaskBoard.vue'
import UsagePanel from './components/UsagePanel.vue'

// Lazy-load heavy components
const SkillsList = defineAsyncComponent(() => import('./components/SkillsList.vue'))
const SoulEditor = defineAsyncComponent(() => import('./components/SoulEditor.vue'))
const ActivityCalendar = defineAsyncComponent(() => import('./components/ActivityCalendar.vue'))

const store = useWarRoomStore()

const tabs = [
  { id: 'kanban',   label: 'Kanban',          icon: 'kanban'    },
  { id: 'usage',    label: 'Usage & Model',   icon: 'cpu'       },
  { id: 'skills',   label: 'Skills',          icon: 'sparkles'  },
  { id: 'soul',     label: 'Soul & Identity', icon: 'file-text' },
  { id: 'calendar', label: 'Calendar',        icon: 'calendar'  },
] as const

type TabId = (typeof tabs)[number]['id']

const activeTab = ref<TabId>('kanban')
const visitedTabs = ref<Set<TabId>>(new Set(['kanban']))

function switchTab(id: TabId) {
  activeTab.value = id
  visitedTabs.value.add(id)
}

onMounted(async () => {
  // Load core data on mount
  await Promise.all([
    store.fetchTasks(),
    store.fetchProjects(),
    store.fetchTags(),
    store.fetchHeartbeat(),
  ])
})
</script>

<style scoped>
.warroom-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 1rem;
}

.tab-bar {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  padding-bottom: 0;
  flex-shrink: 0;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.85rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--mc-text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all var(--mc-transition-speed);
  margin-bottom: -1px;
  white-space: nowrap;
}
.tab-btn:hover { color: var(--mc-text); }
.tab-btn.active {
  color: var(--mc-accent);
  border-bottom-color: var(--mc-accent);
}

.tab-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.tab-panel {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-title {
  font-family: var(--mc-font-display);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--mc-text);
  margin: 0;
}

.loading-placeholder {
  color: var(--mc-text-muted);
  font-size: 0.8rem;
  padding: 2rem 0;
}
</style>
