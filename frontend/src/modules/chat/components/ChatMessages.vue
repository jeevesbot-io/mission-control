<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import type { ChatMessage } from '../store'

const props = defineProps<{
  messages: ChatMessage[]
  sending: boolean
}>()

const container = ref<HTMLElement | null>(null)

function renderMarkdown(content: string): string {
  return marked.parse(content, { async: false }) as string
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight
    }
  },
)

watch(
  () => props.sending,
  async () => {
    await nextTick()
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight
    }
  },
)
</script>

<template>
  <div class="chat-messages" ref="container">
    <div v-if="messages.length === 0" class="chat-messages__empty">
      <span class="chat-messages__empty-icon">💬</span>
      <p>Ask Jeeves anything</p>
    </div>

    <div
      v-for="(msg, i) in messages"
      :key="i"
      class="chat-messages__bubble"
      :class="`chat-messages__bubble--${msg.role}`"
    >
      <div
        v-if="msg.role === 'assistant'"
        class="mc-prose chat-messages__content"
        v-html="renderMarkdown(msg.content)"
      />
      <div v-else-if="msg.role === 'system'" class="chat-messages__content chat-messages__content--system">
        {{ msg.content }}
      </div>
      <div v-else class="chat-messages__content">
        {{ msg.content }}
      </div>
    </div>

    <div v-if="sending" class="chat-messages__thinking">
      <span class="chat-messages__dot" />
      <span class="chat-messages__dot" />
      <span class="chat-messages__dot" />
    </div>
  </div>
</template>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-messages__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--mc-text-muted);
  font-size: 0.875rem;
}

.chat-messages__empty-icon {
  font-size: 2rem;
  opacity: 0.5;
}

.chat-messages__bubble {
  max-width: 85%;
  animation: mc-fade-up 0.2s ease-out;
}

.chat-messages__bubble--user {
  align-self: flex-end;
}

.chat-messages__bubble--user .chat-messages__content {
  background: var(--mc-accent);
  color: #fff;
  padding: 0.625rem 0.875rem;
  border-radius: var(--mc-radius) var(--mc-radius) 4px var(--mc-radius);
  font-size: 0.875rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-messages__bubble--assistant {
  align-self: flex-start;
}

.chat-messages__bubble--assistant .chat-messages__content {
  background: var(--mc-bg-elevated);
  border: 1px solid var(--mc-border);
  padding: 0.625rem 0.875rem;
  border-radius: var(--mc-radius) var(--mc-radius) var(--mc-radius) 4px;
  font-size: 0.875rem;
  line-height: 1.5;
}

.chat-messages__bubble--system {
  align-self: center;
}

.chat-messages__content--system {
  background: none;
  color: var(--mc-warning);
  font-size: 0.8rem;
  text-align: center;
  padding: 0.375rem 0.75rem;
  border-radius: var(--mc-radius-sm);
  border: 1px solid var(--mc-warning);
  opacity: 0.8;
}

/* Thinking dots */
.chat-messages__thinking {
  align-self: flex-start;
  display: flex;
  gap: 4px;
  padding: 0.75rem 1rem;
  background: var(--mc-bg-elevated);
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius);
}

.chat-messages__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--mc-text-muted);
  animation: chat-dot-bounce 1.4s ease-in-out infinite;
}

.chat-messages__dot:nth-child(2) {
  animation-delay: 0.2s;
}

.chat-messages__dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes chat-dot-bounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* Prose overrides for compact chat bubbles */
.chat-messages__content :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-messages__content :deep(pre) {
  font-size: 0.8rem;
}
</style>
