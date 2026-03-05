<script setup lang="ts">
import { computed } from 'vue'
import { isNamedColor } from '@/composables/useNamedColor'

const props = withDefaults(
  defineProps<{
    variant?: 'flat' | 'elevated' | 'interactive'
    accentColor?: string
    accentPosition?: 'top' | 'left' | 'none'
    padding?: 'none' | 'sm' | 'md' | 'lg'
  }>(),
  {
    variant: 'flat',
    accentPosition: 'none',
    padding: 'md',
  },
)

const accentVar = computed(() => {
  if (!props.accentColor) return undefined
  if (isNamedColor(props.accentColor)) return `var(--mc-color-${props.accentColor})`
  return props.accentColor
})
</script>

<template>
  <div
    class="mc-card"
    :class="[
      `mc-card--${variant}`,
      `mc-card--pad-${padding}`,
      accentPosition !== 'none' && accentColor ? `mc-card--accent-${accentPosition}` : '',
    ]"
    :style="accentVar ? { '--_accent': accentVar } as any : undefined"
  >
    <slot />
  </div>
</template>

<style scoped>
.mc-card {
  position: relative;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
}

/* Padding */
.mc-card--pad-none { padding: 0; }
.mc-card--pad-sm { padding: var(--mc-space-3); }
.mc-card--pad-md { padding: var(--mc-space-4); }
.mc-card--pad-lg { padding: var(--mc-space-6); }

/* Variants */
.mc-card--elevated {
  background: var(--mc-bg-elevated);
  box-shadow: var(--mc-shadow-md);
}

.mc-card--interactive {
  cursor: pointer;
  transition:
    background var(--mc-transition-speed) var(--mc-ease-out),
    border-color var(--mc-transition-speed) var(--mc-ease-out),
    box-shadow var(--mc-transition-speed) var(--mc-ease-out);
}

.mc-card--interactive:hover {
  background: var(--mc-bg-elevated);
  border-color: var(--mc-border-strong);
  box-shadow: var(--mc-shadow-sm);
}

/* Accent — top border */
.mc-card--accent-top::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--_accent, var(--mc-accent));
}

/* Accent — left border */
.mc-card--accent-left::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 3px;
  background: var(--_accent, var(--mc-accent));
  border-radius: 3px 0 0 3px;
}
</style>
