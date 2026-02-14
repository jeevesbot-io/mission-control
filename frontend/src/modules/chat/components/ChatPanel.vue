<script setup lang="ts">
import { useChatStore } from '../store'
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'

const store = useChatStore()
</script>

<template>
  <Transition name="chat-panel">
    <div v-if="store.panelOpen" class="chat-panel">
      <div class="chat-panel__header">
        <span class="chat-panel__title">Chat with Jeeves</span>
        <div class="chat-panel__actions">
          <button
            class="chat-panel__btn"
            @click="store.clearMessages()"
            title="New conversation"
          >
            <i class="pi pi-refresh" />
          </button>
          <button
            class="chat-panel__btn"
            @click="store.togglePanel()"
            title="Close"
          >
            <i class="pi pi-times" />
          </button>
        </div>
      </div>

      <ChatMessages :messages="store.messages" :sending="store.sending" />
      <ChatInput :disabled="store.sending" @send="store.sendMessage" />
    </div>
  </Transition>
</template>

<style scoped>
.chat-panel {
  position: fixed;
  top: var(--mc-header-height);
  right: 0;
  width: 380px;
  max-height: calc(100vh - var(--mc-header-height) - 24px);
  display: flex;
  flex-direction: column;
  background: var(--mc-bg-surface);
  backdrop-filter: var(--mc-glass-blur);
  border-left: 1px solid var(--mc-border);
  border-bottom: 1px solid var(--mc-border);
  border-radius: 0 0 0 var(--mc-radius);
  box-shadow: var(--mc-shadow-md);
  z-index: 100;
  overflow: hidden;
}

@media (max-width: 640px) {
  .chat-panel {
    width: 100%;
    max-height: calc(100vh - var(--mc-header-height));
    border-radius: 0;
    border-left: none;
  }
}

.chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--mc-border);
  flex-shrink: 0;
}

.chat-panel__title {
  font-family: var(--mc-font-display);
  font-weight: 600;
  font-size: 0.875rem;
}

.chat-panel__actions {
  display: flex;
  gap: 0.25rem;
}

.chat-panel__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  color: var(--mc-text-muted);
  cursor: pointer;
  border-radius: var(--mc-radius-sm);
  font-size: 0.8rem;
  transition:
    color var(--mc-transition-speed),
    background var(--mc-transition-speed);
}

.chat-panel__btn:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
}

/* Slide transition */
.chat-panel-enter-active,
.chat-panel-leave-active {
  transition:
    transform 0.25s ease,
    opacity 0.25s ease;
}

.chat-panel-enter-from,
.chat-panel-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
