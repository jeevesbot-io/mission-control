import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

interface ChatApiResponse {
  message: ChatMessage
  usage: Record<string, number> | null
}

interface ChatHealthResponse {
  available: boolean
  gateway_url: string
}

export type { ChatMessage }

function generateSessionKey(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  // Fallback for non-secure contexts (e.g. HTTP over Tailscale)
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

function getOrCreateSessionKey(): string {
  let key = sessionStorage.getItem('mc-chat-session')
  if (!key) {
    key = generateSessionKey()
    sessionStorage.setItem('mc-chat-session', key)
  }
  return key
}

export const useChatStore = defineStore('chat', () => {
  const api = useApi()

  const messages = ref<ChatMessage[]>([])
  const sending = ref(false)
  const error = ref<string | null>(null)
  const gatewayAvailable = ref<boolean | null>(null)
  const panelOpen = ref(false)
  const sessionKey = ref(getOrCreateSessionKey())

  async function sendMessage(content: string) {
    if (!content.trim() || sending.value) return

    error.value = null
    messages.value.push({ role: 'user', content: content.trim() })
    sending.value = true

    try {
      const resp = await api.post<ChatApiResponse>('/api/chat/send', {
        messages: messages.value,
        session_key: sessionKey.value,
      })
      messages.value.push(resp.message)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to send message'
      error.value = msg
      messages.value.push({ role: 'system', content: msg })
    } finally {
      sending.value = false
    }
  }

  async function checkHealth() {
    try {
      const resp = await api.get<ChatHealthResponse>('/api/chat/health')
      gatewayAvailable.value = resp.available
    } catch {
      gatewayAvailable.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    error.value = null
    const newKey = generateSessionKey()
    sessionStorage.setItem('mc-chat-session', newKey)
    sessionKey.value = newKey
  }

  function togglePanel() {
    panelOpen.value = !panelOpen.value
  }

  return {
    messages,
    sending,
    error,
    gatewayAvailable,
    panelOpen,
    sessionKey,
    sendMessage,
    checkHealth,
    clearMessages,
    togglePanel,
  }
})
