import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from './store'

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
  mockFetch.mockReset()
  // Mock sessionStorage
  const store: Record<string, string> = {}
  vi.stubGlobal('sessionStorage', {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
  })
  // Mock crypto.randomUUID
  vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid-' + Math.random().toString(36).slice(2, 8) })
})

function mockJsonResponse(data: unknown, status = 200) {
  return mockFetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  })
}

describe('chat store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('sendMessage', () => {
    it('adds user and assistant messages on success', async () => {
      mockJsonResponse({
        message: { role: 'assistant', content: 'Hello! How can I help?' },
        usage: { total_tokens: 18 },
      })

      const store = useChatStore()
      await store.sendMessage('Hello')

      expect(store.messages).toHaveLength(2)
      expect(store.messages[0]).toEqual({ role: 'user', content: 'Hello' })
      expect(store.messages[1]).toEqual({ role: 'assistant', content: 'Hello! How can I help?' })
      expect(store.sending).toBe(false)
      expect(store.error).toBeNull()
    })

    it('adds system error message on API failure', async () => {
      mockJsonResponse({ detail: 'Gateway error' }, 502)

      const store = useChatStore()
      await store.sendMessage('Hello')

      expect(store.messages).toHaveLength(2)
      expect(store.messages[0].role).toBe('user')
      expect(store.messages[1].role).toBe('system')
      expect(store.error).toBeTruthy()
    })

    it('ignores empty or whitespace input', async () => {
      const store = useChatStore()
      await store.sendMessage('')
      await store.sendMessage('   ')

      expect(store.messages).toHaveLength(0)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('prevents concurrent sends', async () => {
      let resolveFirst: (value: unknown) => void
      const firstPromise = new Promise((resolve) => { resolveFirst = resolve })
      mockFetch.mockReturnValueOnce(firstPromise)

      const store = useChatStore()
      const p1 = store.sendMessage('First')

      // While first is sending, try to send second
      await store.sendMessage('Second')

      // Only the first message should be in the array (second was blocked)
      expect(store.messages).toHaveLength(1)
      expect(store.messages[0].content).toBe('First')

      // Resolve first request
      resolveFirst!({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ message: { role: 'assistant', content: 'Response' }, usage: null }),
        text: () => Promise.resolve(''),
      })
      await p1

      expect(store.messages).toHaveLength(2)
    })
  })

  describe('checkHealth', () => {
    it('sets gatewayAvailable to true when available', async () => {
      mockJsonResponse({ available: true, gateway_url: 'http://localhost:18789' })

      const store = useChatStore()
      await store.checkHealth()

      expect(store.gatewayAvailable).toBe(true)
    })

    it('sets gatewayAvailable to false when unavailable', async () => {
      mockJsonResponse({ available: false, gateway_url: 'http://localhost:18789' })

      const store = useChatStore()
      await store.checkHealth()

      expect(store.gatewayAvailable).toBe(false)
    })
  })

  describe('clearMessages', () => {
    it('resets messages and regenerates session key', async () => {
      mockJsonResponse({
        message: { role: 'assistant', content: 'Hi' },
        usage: null,
      })

      const store = useChatStore()
      await store.sendMessage('Hello')
      const oldKey = store.sessionKey

      store.clearMessages()

      expect(store.messages).toHaveLength(0)
      expect(store.error).toBeNull()
      expect(store.sessionKey).not.toBe(oldKey)
    })
  })

  describe('togglePanel', () => {
    it('toggles panel open state', () => {
      const store = useChatStore()
      expect(store.panelOpen).toBe(false)

      store.togglePanel()
      expect(store.panelOpen).toBe(true)

      store.togglePanel()
      expect(store.panelOpen).toBe(false)
    })
  })
})
