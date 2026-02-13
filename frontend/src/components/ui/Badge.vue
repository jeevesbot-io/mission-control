<script setup lang="ts">
defineProps<{
  variant: 'success' | 'warning' | 'danger' | 'info'
  label: string
}>()
</script>

<template>
  <span class="badge" :class="`badge--${variant}`">{{ label }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.5rem;
  font-family: var(--mc-font-mono);
  font-size: 0.6875rem;
  font-weight: 600;
  border-radius: 4px;
  line-height: 1.6;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.badge--success {
  color: var(--mc-success);
  background: color-mix(in srgb, var(--mc-success) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-success) 20%, transparent);
}

.badge--warning {
  color: var(--mc-warning);
  background: color-mix(in srgb, var(--mc-warning) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-warning) 20%, transparent);
}

.badge--danger {
  color: var(--mc-danger);
  background: color-mix(in srgb, var(--mc-danger) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-danger) 20%, transparent);
}

.badge--info {
  color: var(--mc-info);
  background: color-mix(in srgb, var(--mc-info) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-info) 20%, transparent);
}
</style>
