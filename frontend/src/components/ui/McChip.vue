<script setup lang="ts">
import { computed } from 'vue'
import { isNamedColor } from '@/composables/useNamedColor'
import McIcon from './McIcon.vue'

const props = withDefaults(
  defineProps<{
    color?: string
    variant?: 'default' | 'status' | 'outline'
    size?: 'sm' | 'md'
    removable?: boolean
    mono?: boolean
    uppercase?: boolean
    icon?: string
    dot?: boolean
  }>(),
  {
    variant: 'default',
    size: 'sm',
    removable: false,
    mono: false,
    uppercase: false,
    dot: false,
  },
)

const emit = defineEmits<{ remove: [] }>()

const colorVars = computed(() => {
  if (!props.color) return {}
  if (isNamedColor(props.color)) {
    return {
      '--_chip-color': `var(--mc-color-${props.color})`,
      '--_chip-bg': `var(--mc-color-${props.color}-bg)`,
      '--_chip-border': `var(--mc-color-${props.color}-border)`,
    }
  }
  // Status colors: success, warning, danger, info
  const statusColors = ['success', 'warning', 'danger', 'info']
  if (statusColors.includes(props.color)) {
    return {
      '--_chip-color': `var(--mc-${props.color})`,
      '--_chip-bg': `var(--mc-${props.color}-bg)`,
      '--_chip-border': `var(--mc-${props.color}-border)`,
    }
  }
  return { '--_chip-color': props.color }
})
</script>

<template>
  <span
    class="mc-chip"
    :class="[
      `mc-chip--${variant}`,
      `mc-chip--${size}`,
      { 'mc-chip--mono': mono, 'mc-chip--upper': uppercase },
    ]"
    :style="colorVars"
  >
    <span v-if="dot" class="mc-chip__dot" />
    <McIcon v-if="icon" :name="icon" :size="size === 'sm' ? 12 : 14" />
    <span class="mc-chip__text"><slot /></span>
    <button
      v-if="removable"
      class="mc-chip__remove"
      @click.stop="emit('remove')"
      aria-label="Remove"
    >
      <McIcon name="x" :size="12" />
    </button>
  </span>
</template>

<style scoped>
.mc-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--mc-space-1);
  border-radius: var(--mc-radius-xs);
  font-weight: 500;
  line-height: 1;
  color: var(--_chip-color, var(--mc-text-muted));
  background: var(--_chip-bg, var(--mc-bg-elevated));
  border: 1px solid var(--_chip-border, var(--mc-border));
}

.mc-chip--sm {
  height: 22px;
  padding: 0 var(--mc-space-2);
  font-size: var(--mc-text-xs);
}

.mc-chip--md {
  height: 28px;
  padding: 0 var(--mc-space-3);
  font-size: var(--mc-text-sm);
}

/* Variants */
.mc-chip--outline {
  background: transparent;
}

.mc-chip--status {
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* Modifiers */
.mc-chip--mono {
  font-family: var(--mc-font-mono);
}

.mc-chip--upper {
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Dot indicator */
.mc-chip__dot {
  width: 6px;
  height: 6px;
  border-radius: var(--mc-radius-full);
  background: var(--_chip-color, var(--mc-text-muted));
  flex-shrink: 0;
}

/* Remove button */
.mc-chip__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: var(--mc-space-1);
  margin-right: calc(-1 * var(--mc-space-1));
  padding: 2px;
  background: none;
  border: none;
  color: inherit;
  opacity: 0.5;
  cursor: pointer;
  border-radius: 2px;
  transition: opacity var(--mc-transition-fast);
}

.mc-chip__remove:hover {
  opacity: 1;
}
</style>
