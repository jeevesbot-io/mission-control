<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import AppLayout from '@/components/layout/AppLayout.vue'
import ChatPanel from '@/modules/chat/components/ChatPanel.vue'

const appStore = useAppStore()
</script>

<template>
  <div :class="{ 'dark-mode': appStore.darkMode }">
    <AppLayout>
      <router-view />
    </AppLayout>
    <ChatPanel />
  </div>
</template>
