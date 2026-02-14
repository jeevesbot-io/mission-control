<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'

interface SchoolEvent {
  id: number
  child: string | null
  summary: string
  event_date: string | null
  event_time: string | null
  school_id: string | null
}

const api = useApi()
const events = ref<SchoolEvent[]>([])
const error = ref(false)

onMounted(async () => {
  try {
    const data = await api.get<{ events: SchoolEvent[] }>('/api/school/events')
    events.value = data.events.slice(0, 5)
  } catch {
    error.value = true
  }
})

function childColour(child: string | null): string {
  if (!child) return 'var(--mc-accent)'
  const lower = child.toLowerCase()
  if (lower.includes('natty')) return 'var(--mc-info)'
  if (lower.includes('elodie')) return '#a78bfa'
  if (lower.includes('florence')) return 'var(--mc-success)'
  return 'var(--mc-accent)'
}
</script>

<template>
  <div class="today-events">
    <div class="today-events__header">
      <h3 class="today-events__title">Upcoming Events</h3>
      <RouterLink to="/school" class="today-events__link">View all</RouterLink>
    </div>

    <div v-if="error" class="today-events__error">
      <i class="pi pi-exclamation-triangle" />
      School module unavailable
    </div>

    <div v-else-if="events.length === 0" class="today-events__empty">
      No upcoming events
    </div>

    <div v-else class="today-events__list">
      <div
        v-for="event in events"
        :key="event.id"
        class="today-events__item"
      >
        <div class="today-events__dot" :style="{ background: childColour(event.child) }" />
        <div class="today-events__info">
          <span class="today-events__name">{{ event.summary }}</span>
          <span class="today-events__time mc-mono">
            {{ event.event_date }}
            <template v-if="event.event_time"> · {{ event.event_time }}</template>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.today-events {
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  padding: 1.25rem;
}

.today-events__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.today-events__title {
  font-family: var(--mc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
}

.today-events__link {
  font-size: 0.75rem;
  color: var(--mc-accent);
  text-decoration: none;
}

.today-events__link:hover {
  color: var(--mc-accent-hover);
}

.today-events__list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.today-events__item {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.4rem 0;
}

.today-events__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 0.35rem;
  flex-shrink: 0;
}

.today-events__info {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.today-events__name {
  font-size: 0.85rem;
  font-weight: 500;
}

.today-events__time {
  font-size: 0.7rem;
  color: var(--mc-text-muted);
}

.today-events__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--mc-warning);
  padding: 0.5rem;
}

.today-events__empty {
  font-size: 0.8rem;
  color: var(--mc-text-muted);
  padding: 0.5rem;
}
</style>
