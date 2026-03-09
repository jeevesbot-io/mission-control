<script setup lang="ts">
import { onMounted } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'

// Dark-only — apply to <html> so PrimeVue teleported overlays
// (Dialog, Select dropdown, Popover, etc.) inherit the dark theme.
onMounted(() => {
  document.documentElement.setAttribute('data-theme', 'dark')
  document.documentElement.classList.add('dark-mode')
})
</script>

<template>
  <AppLayout>
    <router-view />
  </AppLayout>
</template>
