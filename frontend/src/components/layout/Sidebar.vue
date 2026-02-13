<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { moduleRegistry } from '@/router'
import { useRoute } from 'vue-router'

const appStore = useAppStore()
const route = useRoute()

defineProps<{
  mobileOpen: boolean
}>()

const emit = defineEmits<{
  closeMobile: []
}>()

function isActive(moduleId: string): boolean {
  if (moduleId === 'overview') return route.path === '/'
  return route.path.startsWith(`/${moduleId}`)
}
</script>

<template>
  <!-- Mobile backdrop -->
  <Transition name="backdrop">
    <div v-if="mobileOpen" class="sidebar-backdrop" @click="emit('closeMobile')" />
  </Transition>

  <aside
    class="sidebar"
    :class="{
      'sidebar--collapsed': appStore.sidebarCollapsed,
      'sidebar--mobile-open': mobileOpen,
    }"
  >
    <!-- Brand -->
    <div class="sidebar__brand">
      <div class="sidebar__brand-mark">
        <div class="sidebar__brand-ring" />
        <span class="sidebar__brand-icon">&#x1f9e0;</span>
      </div>
      <Transition name="label-fade">
        <div v-show="!appStore.sidebarCollapsed" class="sidebar__brand-info">
          <span class="sidebar__brand-text">Mission Control</span>
          <span class="sidebar__brand-tag">GROUND CONTROL</span>
        </div>
      </Transition>
    </div>

    <!-- Navigation -->
    <nav class="sidebar__nav">
      <RouterLink
        v-for="mod in moduleRegistry"
        :key="mod.id"
        :to="mod.id === 'overview' ? '/' : `/${mod.id}`"
        class="sidebar__link"
        :class="{ 'sidebar__link--active': isActive(mod.id) }"
        @click="emit('closeMobile')"
      >
        <span class="sidebar__link-indicator" />
        <span class="sidebar__link-icon">{{ mod.icon }}</span>
        <Transition name="label-fade">
          <span v-show="!appStore.sidebarCollapsed" class="sidebar__link-label">{{ mod.name }}</span>
        </Transition>
      </RouterLink>
    </nav>

    <!-- Bottom controls -->
    <div class="sidebar__footer">
      <button class="sidebar__collapse-btn" @click="appStore.toggleSidebar" title="Toggle sidebar">
        <i :class="appStore.sidebarCollapsed ? 'pi pi-angle-double-right' : 'pi pi-angle-double-left'" />
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* Backdrop */
.sidebar-backdrop {
  display: none;
}

@media (max-width: 640px) {
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: 40;
  }
}

.backdrop-enter-active,
.backdrop-leave-active {
  transition: opacity var(--mc-transition-speed);
}

.backdrop-enter-from,
.backdrop-leave-to {
  opacity: 0;
}

/* Label fade transition */
.label-fade-enter-active {
  transition: opacity 150ms ease 80ms;
}

.label-fade-leave-active {
  transition: opacity 80ms ease;
}

.label-fade-enter-from,
.label-fade-leave-to {
  opacity: 0;
}

/* Sidebar */
.sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
  width: var(--mc-sidebar-width);
  height: 100vh;
  background: var(--mc-bg-surface);
  backdrop-filter: var(--mc-glass-blur);
  border-right: 1px solid var(--mc-border);
  transition: width var(--mc-transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
  z-index: 50;
}

/* Right edge accent line */
.sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    var(--mc-accent) 30%,
    var(--mc-accent) 70%,
    transparent 100%
  );
  opacity: 0.15;
}

.sidebar--collapsed {
  width: var(--mc-sidebar-collapsed-width);
}

/* Mobile */
@media (max-width: 640px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    transform: translateX(-100%);
    transition: transform var(--mc-transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
    width: 280px;
  }

  .sidebar--mobile-open {
    transform: translateX(0);
  }

  .sidebar--collapsed {
    width: 280px;
  }

  .sidebar__collapse-btn {
    display: none !important;
  }

  /* Show labels on mobile regardless of collapsed state */
  .sidebar--collapsed .sidebar__brand-info,
  .sidebar--collapsed .sidebar__link-label {
    display: block !important;
  }
}

/* Brand */
.sidebar__brand {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  height: var(--mc-header-height);
  overflow: hidden;
  white-space: nowrap;
}

.sidebar__brand-mark {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.sidebar__brand-ring {
  position: absolute;
  inset: 0;
  border-radius: 10px;
  border: 1.5px solid var(--mc-accent);
  opacity: 0.35;
  animation: mc-glow-pulse 4s ease-in-out infinite;
}

.sidebar__brand-icon {
  font-size: 1.25rem;
  position: relative;
  z-index: 1;
}

.sidebar__brand-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar__brand-text {
  font-family: var(--mc-font-display);
  font-size: 0.9375rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.sidebar__brand-tag {
  font-family: var(--mc-font-mono);
  font-size: 0.5625rem;
  font-weight: 600;
  color: var(--mc-accent);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  line-height: 1.4;
}

/* Nav */
.sidebar__nav {
  flex: 1;
  padding: 0.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar__link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.625rem 0.75rem;
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text-muted);
  text-decoration: none;
  transition:
    background var(--mc-transition-speed),
    color var(--mc-transition-speed);
  overflow: hidden;
  white-space: nowrap;
}

.sidebar__link:hover {
  background: var(--mc-bg-hover);
  color: var(--mc-text);
}

/* Active indicator bar */
.sidebar__link-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  border-radius: 0 2px 2px 0;
  background: var(--mc-accent);
  transition:
    height var(--mc-transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar__link--active .sidebar__link-indicator {
  height: 60%;
}

.sidebar__link--active {
  background: var(--mc-accent-subtle);
  color: var(--mc-accent);
}

.sidebar__link-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  width: 32px;
  text-align: center;
}

.sidebar__link-label {
  font-size: 0.875rem;
  font-weight: 500;
}

/* Footer */
.sidebar__footer {
  padding: 0.5rem;
  border-top: 1px solid var(--mc-border);
}

.sidebar__collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 36px;
  border: none;
  background: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  border-radius: var(--mc-radius-sm);
  font-size: 0.875rem;
  transition:
    color var(--mc-transition-speed),
    background var(--mc-transition-speed);
}

.sidebar__collapse-btn:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
}
</style>
