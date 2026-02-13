<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, nextTick, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { marked } from 'marked'
import { useMemoryStore } from './store'
import PageShell from '@/components/layout/PageShell.vue'

const store = useMemoryStore()
const activeSlug = ref('')
const contentEl = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

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
  if (!store.longTerm) return ''
  return marked.parse(store.longTerm.content) as string
})

const tocSections = computed(() => {
  if (!store.longTerm) return []
  return store.longTerm.sections.filter((s) => s.level >= 2)
})

function setupObserver() {
  if (observer) observer.disconnect()
  if (!contentEl.value) return

  const headings = contentEl.value.querySelectorAll('h2, h3, h4, h5, h6')
  if (headings.length === 0) return

  observer = new IntersectionObserver(
    (entries) => {
      // Find the topmost visible heading
      for (const entry of entries) {
        if (entry.isIntersecting) {
          activeSlug.value = entry.target.id
          break
        }
      }
    },
    {
      rootMargin: '-80px 0px -70% 0px',
      threshold: 0,
    },
  )

  headings.forEach((h) => observer!.observe(h))
}

onMounted(async () => {
  await store.fetchLongTerm()
  await nextTick()
  setupObserver()
})

watch(renderedContent, async () => {
  await nextTick()
  setupObserver()
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<template>
  <PageShell>
    <div class="lt-page">
      <!-- Sticky TOC sidebar -->
      <aside v-if="tocSections.length > 0" class="lt-page__toc">
        <h4 class="lt-page__toc-title">Contents</h4>
        <nav>
          <a
            v-for="section in tocSections"
            :key="section.slug"
            :href="`#${section.slug}`"
            class="lt-page__toc-link"
            :class="{
              'lt-page__toc-link--active': activeSlug === section.slug,
              'lt-page__toc-link--sub': section.level > 2,
            }"
          >
            {{ section.heading }}
          </a>
        </nav>
      </aside>

      <!-- Main content -->
      <div class="lt-page__main">
        <div class="lt-page__nav">
          <RouterLink to="/memory" class="lt-page__back">
            <i class="pi pi-arrow-left" />
            Memory
          </RouterLink>
        </div>

        <h2 class="lt-page__heading">
          <span class="lt-page__heading-icon">🧠</span>
          Long-Term Memory
        </h2>

        <div v-if="store.loading" class="lt-page__loading">
          <i class="pi pi-spin pi-spinner" />
          Loading...
        </div>

        <div v-else-if="store.error" class="lt-page__error">
          <i class="pi pi-exclamation-triangle" />
          {{ store.error }}
        </div>

        <div
          v-else-if="store.longTerm"
          ref="contentEl"
          class="mc-prose"
          v-html="renderedContent"
        />
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.lt-page {
  display: flex;
  gap: 2rem;
  max-width: 1100px;
}

/* Sticky TOC */
.lt-page__toc {
  position: sticky;
  top: 1rem;
  flex-shrink: 0;
  width: 220px;
  max-height: calc(100vh - 6rem);
  overflow-y: auto;
  align-self: flex-start;
}

.lt-page__toc-title {
  font-family: var(--mc-font-display);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--mc-text-muted);
  margin-bottom: 0.5rem;
}

.lt-page__toc-link {
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

.lt-page__toc-link:hover {
  color: var(--mc-accent);
  border-left-color: var(--mc-accent);
}

.lt-page__toc-link--active {
  color: var(--mc-accent);
  border-left-color: var(--mc-accent);
  font-weight: 500;
}

.lt-page__toc-link--sub {
  padding-left: 1rem;
  font-size: 0.75rem;
}

/* Main */
.lt-page__main {
  flex: 1;
  min-width: 0;
  max-width: 720px;
}

.lt-page__nav {
  margin-bottom: 1rem;
}

.lt-page__back {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--mc-text-muted);
  text-decoration: none;
  transition: color var(--mc-transition-speed);
}

.lt-page__back:hover {
  color: var(--mc-accent);
}

.lt-page__heading {
  font-family: var(--mc-font-display);
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.lt-page__heading-icon {
  font-size: 1.2rem;
}

.lt-page__loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--mc-text-muted);
  padding: 2rem 0;
}

.lt-page__error {
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
  .lt-page {
    flex-direction: column;
  }

  .lt-page__toc {
    position: static;
    width: 100%;
    max-height: none;
    border-bottom: 1px solid var(--mc-border);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
  }
}
</style>
