<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
}>()

const input = ref('')
const textarea = ref<HTMLTextAreaElement | null>(null)

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function send() {
  const content = input.value.trim()
  if (!content || props.disabled) return
  emit('send', content)
  input.value = ''
  nextTick(autoGrow)
}

function autoGrow() {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 96) + 'px' // max ~4 lines
}

watch(input, () => nextTick(autoGrow))
</script>

<template>
  <div class="chat-input">
    <textarea
      ref="textarea"
      v-model="input"
      class="chat-input__textarea"
      placeholder="Message Jeeves..."
      rows="1"
      :disabled="disabled"
      @keydown="handleKeydown"
    />
    <button
      class="chat-input__send"
      :disabled="disabled || !input.trim()"
      @click="send"
      title="Send message"
    >
      <i class="pi pi-send" />
    </button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--mc-border);
  background: var(--mc-bg-surface);
}

.chat-input__textarea {
  flex: 1;
  resize: none;
  border: 1px solid var(--mc-border);
  background: var(--mc-bg-elevated);
  color: var(--mc-text);
  font-family: var(--mc-font-body);
  font-size: 0.875rem;
  line-height: 1.5;
  padding: 0.5rem 0.75rem;
  border-radius: var(--mc-radius-sm);
  outline: none;
  transition: border-color var(--mc-transition-speed);
  overflow-y: auto;
}

.chat-input__textarea:focus {
  border-color: var(--mc-accent);
}

.chat-input__textarea::placeholder {
  color: var(--mc-text-muted);
}

.chat-input__textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input__send {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: var(--mc-accent);
  color: #fff;
  border-radius: var(--mc-radius-sm);
  cursor: pointer;
  font-size: 0.875rem;
  transition:
    background var(--mc-transition-speed),
    opacity var(--mc-transition-speed);
  flex-shrink: 0;
}

.chat-input__send:hover:not(:disabled) {
  background: var(--mc-accent-hover);
}

.chat-input__send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
