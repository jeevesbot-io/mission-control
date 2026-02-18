<template>
  <span v-if="project" class="project-badge" :style="badgeStyle">
    {{ project.name }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Project } from '../store'

const props = defineProps<{ project: Project | null | undefined }>()

const COLOR_MAP: Record<string, { bg: string; border: string; text: string }> = {
  purple: { bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.3)', text: '#a78bfa' },
  pink:   { bg: 'rgba(244,114,182,0.12)', border: 'rgba(244,114,182,0.3)', text: '#f472b6' },
  green:  { bg: 'rgba(52,211,153,0.12)',  border: 'rgba(52,211,153,0.3)',  text: '#34d399' },
  blue:   { bg: 'rgba(96,165,250,0.12)',  border: 'rgba(96,165,250,0.3)',  text: '#60a5fa' },
  amber:  { bg: 'rgba(251,191,36,0.12)',  border: 'rgba(251,191,36,0.3)',  text: '#fbbf24' },
  indigo: { bg: 'rgba(129,140,248,0.12)', border: 'rgba(129,140,248,0.3)', text: '#818cf8' },
  red:    { bg: 'rgba(248,113,113,0.12)', border: 'rgba(248,113,113,0.3)', text: '#f87171' },
  orange: { bg: 'rgba(251,146,60,0.12)',  border: 'rgba(251,146,60,0.3)',  text: '#fb923c' },
  cyan:   { bg: 'rgba(34,211,238,0.12)',  border: 'rgba(34,211,238,0.3)',  text: '#22d3ee' },
  yellow: { bg: 'rgba(253,224,71,0.12)',  border: 'rgba(253,224,71,0.3)',  text: '#fde047' },
}

const badgeStyle = computed(() => {
  if (!props.project) return {}
  const c = COLOR_MAP[props.project.color] ?? COLOR_MAP['purple']
  return {
    backgroundColor: c.bg,
    borderColor: c.border,
    color: c.text,
  }
})
</script>

<style scoped>
.project-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-family: var(--mc-font-mono);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}
</style>
