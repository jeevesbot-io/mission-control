<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    options: Array<{ value: string; label: string; icon?: string; count?: number }>
    modelValue: string | string[]
    multiple?: boolean
    label?: string
  }>(),
  { multiple: false },
)

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]]
}>()

function isSelected(value: string): boolean {
  if (Array.isArray(props.modelValue)) return props.modelValue.includes(value)
  return props.modelValue === value
}

function toggle(value: string) {
  if (props.multiple && Array.isArray(props.modelValue)) {
    const next = isSelected(value)
      ? props.modelValue.filter((v) => v !== value)
      : [...props.modelValue, value]
    emit('update:modelValue', next)
  } else {
    emit('update:modelValue', value)
  }
}
</script>

<template>
  <div class="mc-filter" role="group" :aria-label="label ?? 'Filter'">
    <span v-if="label" class="mc-filter__label">{{ label }}</span>
    <div class="mc-filter__pills">
      <button
        v-for="opt in options"
        :key="opt.value"
        class="mc-filter__pill"
        :class="{ 'mc-filter__pill--active': isSelected(opt.value) }"
        :aria-pressed="isSelected(opt.value)"
        @click="toggle(opt.value)"
      >
        {{ opt.label }}
        <span v-if="opt.count != null" class="mc-filter__count">{{ opt.count }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.mc-filter {
  display: flex;
  align-items: center;
  gap: var(--mc-space-3);
}

.mc-filter__label {
  font-size: var(--mc-text-xs);
  font-weight: 600;
  color: var(--mc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.mc-filter__pills {
  display: flex;
  gap: var(--mc-space-1);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.mc-filter__pills::-webkit-scrollbar {
  display: none;
}

.mc-filter__pill {
  display: inline-flex;
  align-items: center;
  gap: var(--mc-space-1);
  height: 30px;
  padding: 0 var(--mc-space-3);
  font-family: var(--mc-font-body);
  font-size: var(--mc-text-xs);
  font-weight: 500;
  color: var(--mc-text-muted);
  background: transparent;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-full);
  cursor: pointer;
  white-space: nowrap;
  transition:
    background var(--mc-transition-fast),
    color var(--mc-transition-fast),
    border-color var(--mc-transition-fast);
}

.mc-filter__pill:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
}

.mc-filter__pill--active {
  color: var(--mc-accent);
  background: var(--mc-accent-subtle);
  border-color: var(--mc-accent-glow);
}

.mc-filter__count {
  font-family: var(--mc-font-mono);
  font-size: 0.625rem;
  opacity: 0.6;
}
</style>
