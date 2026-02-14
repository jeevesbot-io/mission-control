<script setup lang="ts">
import { computed } from 'vue'
import { resolveIcon } from '@/composables/useIcons'

const props = withDefaults(
  defineProps<{
    name: string
    size?: number
    strokeWidth?: number
    accent?: string
    boxed?: boolean
  }>(),
  {
    size: 20,
    strokeWidth: 2,
    boxed: false,
  },
)

const iconComponent = computed(() => resolveIcon(props.name))
</script>

<template>
  <span
    v-if="boxed && iconComponent"
    class="mc-icon-box"
    :style="{
      '--mc-icon-accent': accent ?? 'var(--mc-accent)',
      width: '40px',
      height: '40px',
    }"
  >
    <component
      :is="iconComponent"
      :size="size"
      :stroke-width="strokeWidth"
      class="mc-icon-box__svg"
    />
  </span>
  <component
    v-else-if="iconComponent"
    :is="iconComponent"
    :size="size"
    :stroke-width="strokeWidth"
    class="mc-icon"
  />
</template>

<style scoped>
.mc-icon {
  display: inline-flex;
  flex-shrink: 0;
  vertical-align: middle;
}

.mc-icon-box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: color-mix(in srgb, var(--mc-icon-accent) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--mc-icon-accent) 20%, transparent);
  flex-shrink: 0;
}

.mc-icon-box__svg {
  color: var(--mc-icon-accent);
}
</style>
