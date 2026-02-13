<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { marked } from 'marked'
import { useMemoryStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'

const route = useRoute()
const store = useMemoryStore()

const date = computed(() => route.params.date as string)

// Custom renderer that adds id slugs to headings
const renderer = new marked.Renderer()
renderer.heading = ({ text, depth }: { text: string; depth: number }) => {
  const slug = text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return `<h${depth} id="${slug}">${text}</h${depth}>`
}
marked.use({ renderer })

const renderedContent = computed(() => {
  if (!store.currentDaily) return ''
  return marked.parse(store.currentDaily.content) as string
})

// Prev/next navigation
const allDates = computed(() => store.files.map((f) => f.date))
const currentIndex = computed(() => allDates.value.indexOf(date.value))
const prevDate = computed(() => (currentIndex.value < allDates.value.length - 1 ? allDates.value[currentIndex.value + 1] : null))
const nextDate = computed(() => (currentIndex.value > 0 ? allDates.value[currentIndex.value - 1] : null))

// TOC sections (skip H1 title)
const tocSections = computed(() => {
  if (!store.currentDaily) return []
  return store.currentDaily.sections.filter((s) => s.level >= 2)
})

onMounted(() => {
  store.fetchDaily(date.value)
  if (store.files.length === 0) store.fetchFiles()
})

watch(date, (newDate) => {
  store.fetchDaily(newDate)
})
</script>

<template>
  <PageShell>
    <div class="daily-page">
      <!-- Sidebar TOC -->
      <aside v-if="tocSections.length > 0" class="daily-page__toc">
        <h4 class="daily-page__toc-title">Sections</h4>
        <nav>
          <a
            v-for="section in tocSections"
            :key="section.slug"
            :href="`#${section.slug}`"
            class="daily-page__toc-link"
            :class="{ 'daily-page__toc-link--sub': section.level > 2 }"
          >
            {{ section.heading }}
          </a>
        </nav>
      </aside>

      <!-- Main content -->
      <div class="daily-page__main">
        <!-- Nav bar -->
        <div class="daily-page__nav">
          <RouterLink to="/memory" class="daily-page__back">
            <i class="pi pi-arrow-left" />
            Memory
          </RouterLink>
          <div class="daily-page__nav-arrows">
            <RouterLink
              v-if="prevDate"
              :to="`/memory/daily/${prevDate}`"
              class="daily-page__nav-btn"
              title="Previous day"
            >
              <i class="pi pi-chevron-left" />
            </RouterLink>
            <span v-else class="daily-page__nav-btn daily-page__nav-btn--disabled">
              <i class="pi pi-chevron-left" />
            </span>
            <RouterLink
              v-if="nextDate"
              :to="`/memory/daily/${nextDate}`"
              class="daily-page__nav-btn"
              title="Next day"
            >
              <i class="pi pi-chevron-right" />
            </RouterLink>
            <span v-else class="daily-page__nav-btn daily-page__nav-btn--disabled">
              <i class="pi pi-chevron-right" />
            </span>
          </div>
        </div>

        <!-- Date heading -->
        <h2 class="daily-page__date mc-mono">{{ date }}</h2>

        <!-- Loading -->
        <div v-if="store.loading" class="daily-page__loading">
          <i class="pi pi-spin pi-spinner" />
          Loading...
        </div>

        <!-- Error -->
        <div v-else-if="store.error" class="daily-page__error">
          <i class="pi pi-exclamation-triangle" />
          {{ store.error }}
        </div>

        <!-- Content -->
        <div
          v-else-if="store.currentDaily"
          class="mc-prose"
          v-html="renderedContent"
        />
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.daily-page {
  display: flex;
  gap: 2rem;
  max-width: 1100px;
}

/* TOC sidebar */
.daily-page__toc {
  position: sticky;
  top: 1rem;
  flex-shrink: 0;
  width: 200px;
  max-height: calc(100vh - 6rem);
  overflow-y: auto;
  align-self: flex-start;
}

.daily-page__toc-title {
  font-family: var(--mc-font-display);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--mc-text-muted);
  margin-bottom: 0.5rem;
}

.daily-page__toc-link {
  display: block;
  padding: 0.3rem 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: color var(--mc-transition-speed), border-color var(--mc-transition-speed);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.daily-page__toc-link:hover {
  color: var(--mc-accent);
  border-left-color: var(--mc-accent);
}

.daily-page__toc-link--sub {
  padding-left: 1rem;
  font-size: 0.75rem;
}

/* Main area */
.daily-page__main {
  flex: 1;
  min-width: 0;
  max-width: 720px;
}

/* Nav */
.daily-page__nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.daily-page__back {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  text-decoration: none;
  transition: color var(--mc-transition-speed);
}

.daily-page__back:hover {
  color: var(--mc-accent);
}

.daily-page__nav-arrows {
  display: flex;
  gap: 0.25rem;
}

.daily-page__nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--mc-radius-sm);
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  color: var(--mc-text-muted);
  text-decoration: none;
  transition: all var(--mc-transition-speed);
}

.daily-page__nav-btn:hover {
  border-color: var(--mc-accent);
  color: var(--mc-accent);
}

.daily-page__nav-btn--disabled {
  opacity: 0.3;
  pointer-events: none;
}

/* Date */
.daily-page__date {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--mc-accent);
  margin-bottom: 1.5rem;
}

/* States */
.daily-page__loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--mc-text-muted);
  padding: 2rem 0;
}

.daily-page__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: var(--mc-radius-sm);
  color: var(--mc-danger);
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .daily-page {
    flex-direction: column;
  }

  .daily-page__toc {
    position: static;
    width: 100%;
    max-height: none;
    border-bottom: 1px solid var(--mc-border);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
  }
}
</style>
