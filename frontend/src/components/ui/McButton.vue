<script setup lang="ts">
import McIcon from './McIcon.vue'

withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    icon?: string
    iconRight?: string
    loading?: boolean
    fullWidth?: boolean
    disabled?: boolean
  }>(),
  {
    variant: 'secondary',
    size: 'md',
    loading: false,
    fullWidth: false,
    disabled: false,
  },
)
</script>

<template>
  <button
    class="mc-btn"
    :class="[
      `mc-btn--${variant}`,
      `mc-btn--${size}`,
      { 'mc-btn--full': fullWidth, 'mc-btn--loading': loading },
    ]"
    :disabled="disabled || loading"
  >
    <span v-if="loading" class="mc-btn__spinner" aria-hidden="true" />
    <McIcon v-else-if="icon" :name="icon" :size="size === 'sm' ? 14 : size === 'lg' ? 20 : 16" />
    <span v-if="$slots.default" class="mc-btn__label"><slot /></span>
    <McIcon v-if="iconRight" :name="iconRight" :size="size === 'sm' ? 14 : size === 'lg' ? 20 : 16" />
  </button>
</template>

<style scoped>
.mc-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mc-space-2);
  font-family: var(--mc-font-body);
  font-weight: 600;
  border: 1px solid transparent;
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  white-space: nowrap;
  transition:
    background var(--mc-transition-speed) var(--mc-ease-out),
    color var(--mc-transition-speed) var(--mc-ease-out),
    border-color var(--mc-transition-speed) var(--mc-ease-out),
    box-shadow var(--mc-transition-speed) var(--mc-ease-out);
}

.mc-btn:disabled {
  opacity: var(--mc-disabled-opacity);
  cursor: not-allowed;
}

/* Sizes */
.mc-btn--sm {
  height: 32px;
  padding: 0 var(--mc-space-3);
  font-size: var(--mc-text-xs);
}

.mc-btn--md {
  height: 38px;
  padding: 0 var(--mc-space-4);
  font-size: var(--mc-text-sm);
}

.mc-btn--lg {
  height: 44px;
  padding: 0 var(--mc-space-5);
  font-size: var(--mc-text-base);
}

/* Variants */
.mc-btn--primary {
  background: var(--mc-accent);
  color: var(--mc-text-inverse);
  border-color: var(--mc-accent);
}

.mc-btn--primary:hover:not(:disabled) {
  background: var(--mc-accent-hover);
  border-color: var(--mc-accent-hover);
}

.mc-btn--secondary {
  background: var(--mc-bg-elevated);
  color: var(--mc-text);
  border-color: var(--mc-border-strong);
}

.mc-btn--secondary:hover:not(:disabled) {
  background: var(--mc-bg-hover);
  border-color: var(--mc-border-strong);
}

.mc-btn--ghost {
  background: transparent;
  color: var(--mc-text-muted);
}

.mc-btn--ghost:hover:not(:disabled) {
  background: var(--mc-bg-hover);
  color: var(--mc-text);
}

.mc-btn--danger {
  background: var(--mc-danger-bg);
  color: var(--mc-danger);
  border-color: var(--mc-danger-border);
}

.mc-btn--danger:hover:not(:disabled) {
  background: var(--mc-danger);
  color: var(--mc-text-inverse);
  border-color: var(--mc-danger);
}

/* Full width */
.mc-btn--full {
  width: 100%;
}

/* Loading spinner */
.mc-btn__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: var(--mc-radius-full);
  animation: mc-btn-spin 0.6s linear infinite;
}

@keyframes mc-btn-spin {
  to { transform: rotate(360deg); }
}

.mc-btn--loading {
  pointer-events: none;
}
</style>
