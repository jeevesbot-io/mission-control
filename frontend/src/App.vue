<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import AppLayout from '@/components/layout/AppLayout.vue'

const appStore = useAppStore()
</script>

<template>
  <div :class="{ 'dark-mode': appStore.darkMode }">
    <AppLayout>
      <router-view />
    </AppLayout>
  </div>
</template>
