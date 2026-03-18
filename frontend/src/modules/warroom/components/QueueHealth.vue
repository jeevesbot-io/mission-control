<template>
  <div class="queue-health" :title="tooltipText">
    <span class="qh-dot" :class="dotClass" />
    <span class="qh-depth mc-mono">{{ todoCount }} queued</span>
    <span class="qh-sep">·</span>
    <span class="qh-hb mc-mono">{{ hbLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useWarRoomStore } from '../store'

const store = useWarRoomStore()
const now = ref(Date.now())

let intervalId: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  intervalId = setInterval(() => {
    now.value = Date.now()
  }, 30_000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})

const todoCount = computed(() => {
  return store.tasks.filter(t => t.status === 'todo').length
})

const hbMs = computed(() => {
  const last = store.heartbeat?.lastHeartbeat
  if (!last) return null
  return now.value - last
})

const hbLabel = computed(() => {
  const ms = hbMs.value
  if (ms === null) return 'no heartbeat'
  const min = Math.floor(ms / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const h = Math.floor(min / 60)
  return `${h}h ago`
})

const dotClass = computed(() => {
  const ms = hbMs.value
  if (ms === null) return 'qh-dot--red'
  if (ms < 10 * 60_000) return 'qh-dot--green'
  if (ms < 60 * 60_000) return 'qh-dot--amber'
  return 'qh-dot--red'
})

const tooltipText = computed(() => {
  const last = store.heartbeat?.lastHeartbeat
  if (!last) return `${todoCount.value} tasks queued · No heartbeat recorded`
  return `${todoCount.value} tasks queued · Last heartbeat: ${new Date(last).toLocaleString()}`
})
</script>

<style scoped>
.queue-health {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-full);
  cursor: default;
  flex-shrink: 0;
}

.qh-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.qh-dot--green { background: var(--mc-success); box-shadow: 0 0 4px color-mix(in srgb, var(--mc-success) 50%, transparent); }
.qh-dot--amber { background: var(--mc-warning); }
.qh-dot--red   { background: var(--mc-danger); animation: mc-pulse-subtle 1.5s ease-in-out infinite; }

.qh-depth {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--mc-text);
}

.qh-sep {
  font-size: 0.68rem;
  color: var(--mc-text-muted);
}

.qh-hb {
  font-size: 0.65rem;
  color: var(--mc-text-muted);
}
</style>
