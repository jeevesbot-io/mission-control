<script setup lang="ts">
import { onMounted } from 'vue'
import PageShell from '@/components/layout/PageShell.vue'
import { useChatStore } from './store'
import ChatMessages from './components/ChatMessages.vue'
import ChatInput from './components/ChatInput.vue'

const store = useChatStore()

onMounted(() => {
  store.checkHealth()
})
</script>

<template>
  <PageShell>
    <div class="chat-page">
      <div class="chat-page__header">
        <h2 class="chat-page__title mc-display">Chat with Jeeves</h2>
        <div class="chat-page__controls">
          <span
            class="chat-page__status"
            :class="store.gatewayAvailable === false ? 'chat-page__status--offline' : ''"
          >
            <span class="chat-page__status-dot" />
            {{ store.gatewayAvailable === null ? 'Checking...' : store.gatewayAvailable ? 'Online' : 'Offline' }}
          </span>
          <button class="chat-page__btn" @click="store.clearMessages()">
            <i class="pi pi-refresh" />
            New conversation
          </button>
        </div>
      </div>

      <div class="chat-page__body">
        <ChatMessages :messages="store.messages" :sending="store.sending" />
        <ChatInput :disabled="store.sending" @send="store.sendMessage" />
      </div>
    </div>
  </PageShell>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.chat-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  flex-shrink: 0;
}

.chat-page__title {
  font-size: 1.25rem;
  font-weight: 700;
}

.chat-page__controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.chat-page__status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--mc-text-muted);
  font-family: var(--mc-font-mono);
}

.chat-page__status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--mc-success);
  box-shadow: 0 0 6px var(--mc-success);
}

.chat-page__status--offline .chat-page__status-dot {
  background: var(--mc-danger);
  box-shadow: 0 0 6px var(--mc-danger);
}

.chat-page__btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--mc-border);
  background: var(--mc-bg-elevated);
  color: var(--mc-text-muted);
  font-family: var(--mc-font-body);
  font-size: 0.8rem;
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  transition:
    color var(--mc-transition-speed),
    background var(--mc-transition-speed),
    border-color var(--mc-transition-speed);
}

.chat-page__btn:hover {
  color: var(--mc-text);
  background: var(--mc-bg-hover);
  border-color: var(--mc-border-strong);
}

.chat-page__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--mc-bg-surface);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
  overflow: hidden;
  min-height: 0;
}
</style>
