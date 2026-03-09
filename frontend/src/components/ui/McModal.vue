<script setup lang="ts">
/**
 * McModal — Mission Control modal wrapper.
 * Wraps PrimeVue Dialog with consistent dark-mode theming,
 * design tokens, and standard sizing.
 */
import Dialog from 'primevue/dialog'

withDefaults(
  defineProps<{
    visible: boolean
    header?: string
    width?: string
    dismissable?: boolean
    closable?: boolean
  }>(),
  {
    width: '520px',
    dismissable: true,
    closable: true,
  },
)

defineEmits<{
  (e: 'update:visible', v: boolean): void
}>()
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    :header="header"
    :modal="true"
    :dismissableMask="dismissable"
    :closable="closable"
    :style="{ width }"
    class="mc-modal"
  >
    <template v-if="$slots.header" #header>
      <slot name="header" />
    </template>

    <slot />

    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </Dialog>
</template>

<style>
/* Global styles — Dialog is teleported outside component scope */
.mc-modal.p-dialog {
  background: var(--mc-modal-bg);
  border: 1px solid var(--mc-modal-border);
  border-radius: var(--mc-radius);
  box-shadow: var(--mc-shadow-lg);
  color: var(--mc-text);
}
</style>
