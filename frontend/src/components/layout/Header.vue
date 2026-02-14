<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useChatStore } from '@/modules/chat/store'

const route = useRoute()
const appStore = useAppStore()
const chatStore = useChatStore()

const now = ref(new Date())
let timer: ReturnType<typeof setInterval>

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 30_000)
})

onUnmounted(() => {
  clearInterval(timer)
})

const emit = defineEmits<{
  toggleMobileMenu: []
}>()

const timeStr = computed(() =>
  now.value.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
)

const dateStr = computed(() =>
  now.value.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
)
</script>

<template>
  <header class="header">
    <div class="header__left">
      <button class="header__hamburger" @click="emit('toggleMobileMenu')" aria-label="Toggle navigation">
        <i class="pi pi-bars" />
      </button>
      <h1 class="header__title">{{ route.meta.title ?? 'Mission Control' }}</h1>
    </div>

    <div class="header__right">
      <!-- Live clock -->
      <div class="header__clock">
        <span class="header__clock-dot" />
        <span class="header__clock-time">{{ timeStr }}</span>
        <span class="header__clock-divider">/</span>
        <span class="header__clock-date">{{ dateStr }}</span>
      </div>

      <!-- Chat toggle -->
      <button class="header__icon-btn" @click="chatStore.togglePanel()" title="Chat with Jeeves">
        <i class="pi pi-comments" />
      </button>

      <!-- Theme toggle -->
      <button
        class="header__icon-btn"
        @click="appStore.toggleDarkMode"
        :title="appStore.darkMode ? 'Switch to light mode' : 'Switch to dark mode'"
        :aria-label="appStore.darkMode ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <i :class="appStore.darkMode ? 'pi pi-sun' : 'pi pi-moon'" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--mc-header-height);
  padding: 0 var(--mc-page-padding);
  background: var(--mc-bg-surface);
  backdrop-filter: var(--mc-glass-blur);
  border-bottom: 1px solid var(--mc-border);
  flex-shrink: 0;
  animation: mc-fade-in 0.3s ease-out;
}

.header__left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header__hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  border-radius: var(--mc-radius-sm);
  font-size: 1.125rem;
  transition:
    color var(--mc-transition-speed),
    background var(--mc-transition-speed);
}

.header__hamburger:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
}

@media (max-width: 640px) {
  .header__hamburger {
    display: flex;
  }
}

.header__title {
  font-family: var(--mc-font-display);
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.header__right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Clock */
.header__clock {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--mc-font-mono);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--mc-text-muted);
  padding: 0.375rem 0.75rem;
  background: var(--mc-bg-elevated);
  border-radius: 9999px;
  border: 1px solid var(--mc-border);
}

.header__clock-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--mc-live);
  box-shadow: 0 0 6px var(--mc-live-glow);
  animation: mc-pulse-subtle 2.5s ease-in-out infinite;
}

.header__clock-time {
  color: var(--mc-text);
  font-weight: 600;
}

.header__clock-divider {
  opacity: 0.3;
}

.header__clock-date {
  letter-spacing: 0.02em;
}

@media (max-width: 640px) {
  .header__clock-date,
  .header__clock-divider {
    display: none;
  }
}

/* Icon buttons */
.header__icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--mc-border);
  background: var(--mc-bg-elevated);
  color: var(--mc-text-muted);
  cursor: pointer;
  border-radius: var(--mc-radius-sm);
  font-size: 1rem;
  transition:
    color var(--mc-transition-speed),
    background var(--mc-transition-speed),
    border-color var(--mc-transition-speed);
}

.header__icon-btn:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
  border-color: var(--mc-border-strong);
}
</style>
