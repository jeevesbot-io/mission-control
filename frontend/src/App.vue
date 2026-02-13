<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<template>
  <div :class="{ 'dark-mode': appStore.darkMode }">
    <router-view />
  </div>
</template>
