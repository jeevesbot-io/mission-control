<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'

const api = useApi()
const health = ref<{ status: string; version: string } | null>(null)

onMounted(async () => {
  try {
    health.value = await api.get('/api/health')
  } catch {
    // API not available yet
  }
})
</script>

<template>
  <main style="padding: 2rem;">
    <h1>Mission Control</h1>
    <p style="color: var(--mc-text-muted); margin-top: 0.5rem;">
      Unified dashboard and life operating system
    </p>
    <div v-if="health" style="margin-top: 2rem; padding: 1rem; background: var(--mc-bg-surface); border-radius: 8px; border: 1px solid var(--mc-border);">
      <p>Backend: <strong>{{ health.status }}</strong></p>
      <p>Version: <strong>{{ health.version }}</strong></p>
    </div>
  </main>
</template>
