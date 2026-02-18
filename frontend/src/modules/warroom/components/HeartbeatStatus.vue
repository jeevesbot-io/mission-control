<template>
  <div v-if="heartbeat" class="heartbeat-status" :title="tooltipText">
    <span class="hb-dot" :class="statusClass" />
    <span class="hb-label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useWarRoomStore } from '../store'

const store = useWarRoomStore()
const now = ref(Date.now())

let intervalId: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await store.fetchHeartbeat()
  // Refresh heartbeat status every 60 seconds
  intervalId = setInterval(async () => {
    now.value = Date.now()
    await store.fetchHeartbeat()
  }, 60_000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})

const heartbeat = computed(() => store.heartbeat)

const ageMs = computed(() => {
  const last = heartbeat.value?.lastHeartbeat
  if (!last) return null
  return now.value - last
})

const label = computed(() => {
  const ms = ageMs.value
  if (ms === null) return 'never'
  const min = Math.floor(ms / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const h = Math.floor(min / 60)
  return `${h}h ago`
})

const statusClass = computed(() => {
  const ms = ageMs.value
  if (ms === null) return 'dot-muted'
  if (ms < 10 * 60_000) return 'dot-green'
  if (ms < 60 * 60_000) return 'dot-amber'
  return 'dot-red'
})

const tooltipText = computed(() => {
  const last = heartbeat.value?.lastHeartbeat
  if (!last) return 'No heartbeat recorded'
  return `Last heartbeat: ${new Date(last).toLocaleString()}`
})
</script>

<style scoped>
.heartbeat-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: default;
}

.hb-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-green  { background: var(--mc-success); }
.dot-amber  { background: var(--mc-warning); }
.dot-red    { background: var(--mc-danger); animation: mc-pulse-subtle 1.5s ease-in-out infinite; }
.dot-muted  { background: var(--mc-text-muted); }

.hb-label {
  font-size: 0.65rem;
  font-family: var(--mc-font-mono);
  color: var(--mc-text-muted);
}
</style>
