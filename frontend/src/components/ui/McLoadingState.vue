<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'spinner' | 'skeleton'
    lines?: number
    label?: string
  }>(),
  {
    variant: 'spinner',
    lines: 3,
    label: 'Loading…',
  },
)
</script>

<template>
  <div class="mc-loading" aria-live="polite" :aria-label="label">
    <!-- Spinner -->
    <div v-if="variant === 'spinner'" class="mc-loading__spinner-wrap">
      <div class="mc-loading__spinner" />
      <span v-if="label" class="mc-loading__label">{{ label }}</span>
    </div>

    <!-- Skeleton -->
    <div v-else class="mc-loading__skeleton">
      <div
        v-for="i in lines"
        :key="i"
        class="mc-loading__bone"
        :style="{ width: i === lines ? '60%' : '100%' }"
      />
    </div>
  </div>
</template>

<style scoped>
.mc-loading {
  padding: var(--mc-space-4);
}

/* Spinner */
.mc-loading__spinner-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--mc-space-3);
  padding: var(--mc-space-8) 0;
}

.mc-loading__spinner {
  width: 28px;
  height: 28px;
  border: 2.5px solid var(--mc-border-strong);
  border-top-color: var(--mc-accent);
  border-radius: var(--mc-radius-full);
  animation: mc-btn-spin 0.7s linear infinite;
}

@keyframes mc-btn-spin {
  to { transform: rotate(360deg); }
}

.mc-loading__label {
  font-size: var(--mc-text-sm);
  color: var(--mc-text-muted);
}

/* Skeleton */
.mc-loading__skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--mc-space-3);
}

.mc-loading__bone {
  height: 14px;
  border-radius: var(--mc-radius-xs);
  background: linear-gradient(
    90deg,
    var(--mc-bg-skeleton) 25%,
    var(--mc-bg-hover) 50%,
    var(--mc-bg-skeleton) 75%
  );
  background-size: 200% 100%;
  animation: mc-skeleton-shimmer 1.5s ease-in-out infinite;
}
</style>
