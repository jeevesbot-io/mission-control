import { ref } from 'vue'

export function useWebSocket() {
  const connected = ref(false)
  const messages = ref<unknown[]>([])

  // Stub — full implementation in Phase 4
  return { connected, messages }
}
