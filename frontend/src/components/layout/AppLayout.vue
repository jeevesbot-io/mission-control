<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const mobileMenuOpen = ref(false)

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <div class="app-layout">
    <Sidebar :mobileOpen="mobileMenuOpen" @closeMobile="closeMobileMenu" />
    <div class="app-layout__main">
      <Header @toggleMobileMenu="toggleMobileMenu" />
      <div class="app-layout__content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.app-layout__main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.app-layout__content {
  position: relative;
  flex: 1;
  overflow-y: auto;
}

@media (max-width: 640px) {
  .app-layout {
    flex-direction: column;
  }
}
</style>
