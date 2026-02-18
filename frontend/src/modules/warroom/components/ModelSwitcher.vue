<template>
  <div class="model-switcher">
    <Select
      :model-value="currentModel"
      :options="modelOptions"
      option-label="label"
      option-value="value"
      placeholder="Switch model"
      class="model-select"
      @change="onModelChange"
    />
    <McIcon v-if="switching" name="refresh-cw" :size="14" class="spin" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import Select from 'primevue/select'
import { useWarRoomStore } from '../store'
import McIcon from '@/components/ui/McIcon.vue'

const store = useWarRoomStore()
const switching = ref(false)

const currentModel = computed(() => store.usage?.model?.replace('anthropic/', '') ?? '')

const modelOptions = computed(() =>
  store.models.map((m) => ({ value: m, label: m.replace('anthropic/', '') })),
)

async function onModelChange(evt: { value: string }) {
  if (!evt.value || evt.value === currentModel.value) return
  switching.value = true
  await store.setModel(evt.value)
  await store.fetchUsage()
  switching.value = false
}
</script>

<style scoped>
.model-switcher {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

:deep(.model-select .p-select) {
  font-size: 0.75rem;
  font-family: var(--mc-font-mono);
  min-width: 180px;
}

.spin {
  animation: spin 1s linear infinite;
  color: var(--mc-accent);
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
