<script setup lang="ts">
import McIcon from './McIcon.vue'
import McButton from './McButton.vue'

withDefaults(
  defineProps<{
    message: string
    severity?: 'error' | 'warning'
  }>(),
  { severity: 'error' },
)

const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div
    class="mc-error"
    :class="`mc-error--${severity}`"
    role="alert"
  >
    <McIcon :name="severity === 'error' ? 'circle-x' : 'alert-triangle'" :size="16" />
    <span class="mc-error__msg">{{ message }}</span>
    <McButton
      v-if="$attrs.onRetry !== undefined"
      variant="ghost"
      size="sm"
      icon="refresh-cw"
      @click="emit('retry')"
    >
      Retry
    </McButton>
  </div>
</template>

<style scoped>
.mc-error {
  display: flex;
  align-items: center;
  gap: var(--mc-space-3);
  padding: var(--mc-space-3) var(--mc-space-4);
  border-radius: var(--mc-radius-sm);
  font-size: var(--mc-text-sm);
}

.mc-error--error {
  color: var(--mc-danger);
  background: var(--mc-danger-bg);
  border: 1px solid var(--mc-danger-border);
}

.mc-error--warning {
  color: var(--mc-warning);
  background: var(--mc-warning-bg);
  border: 1px solid var(--mc-warning-border);
}

.mc-error__msg {
  flex: 1;
}
</style>
