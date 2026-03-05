<script setup lang="ts">
import McIcon from './McIcon.vue'
import McButton from './McButton.vue'

defineProps<{
  icon?: string
  title: string
  description?: string
  ctaLabel?: string
}>()

const emit = defineEmits<{ 'cta-click': [] }>()
</script>

<template>
  <div class="mc-empty" role="status">
    <div v-if="icon" class="mc-empty__icon">
      <McIcon :name="icon" :size="32" />
    </div>
    <h3 class="mc-empty__title">{{ title }}</h3>
    <p v-if="description" class="mc-empty__desc">{{ description }}</p>
    <McButton
      v-if="ctaLabel"
      variant="primary"
      size="sm"
      class="mc-empty__cta"
      @click="emit('cta-click')"
    >
      {{ ctaLabel }}
    </McButton>
    <slot />
  </div>
</template>

<style scoped>
.mc-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--mc-space-10) var(--mc-space-4);
  gap: var(--mc-space-3);
}

.mc-empty__icon {
  color: var(--mc-text-muted);
  opacity: 0.5;
}

.mc-empty__title {
  font-family: var(--mc-font-display);
  font-size: var(--mc-text-base);
  font-weight: 600;
  color: var(--mc-text);
}

.mc-empty__desc {
  font-size: var(--mc-text-sm);
  color: var(--mc-text-muted);
  max-width: 320px;
  line-height: 1.5;
}

.mc-empty__cta {
  margin-top: var(--mc-space-2);
}
</style>
