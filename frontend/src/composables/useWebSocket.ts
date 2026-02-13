import { ref, onUnmounted } from 'vue'

interface WsMessage {
  topic: string
  data: Record<string, unknown>
}

type MessageHandler = (data: Record<string, unknown>) => void

const BASE_DELAY = 1000
const MAX_DELAY = 30000
const MAX_MESSAGES = 100

let socket: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let reconnectAttempt = 0
const globalConnected = ref(false)
const globalMessages = ref<WsMessage[]>([])
const subscribers = new Map<string, Set<MessageHandler>>()
let refCount = 0

function getWsUrl(): string {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = location.hostname
  const port = import.meta.env.DEV ? '5055' : location.port
  return `${proto}//${host}:${port}/ws/live`
}

function connect() {
  if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) {
    return
  }

  try {
    socket = new WebSocket(getWsUrl())
  } catch {
    scheduleReconnect()
    return
  }

  socket.onopen = () => {
    globalConnected.value = true
    reconnectAttempt = 0
    // Re-subscribe all active topics
    for (const topic of subscribers.keys()) {
      socket?.send(JSON.stringify({ action: 'subscribe', topic }))
    }
  }

  socket.onmessage = (event) => {
    try {
      const msg: WsMessage = JSON.parse(event.data)
      globalMessages.value = [msg, ...globalMessages.value].slice(0, MAX_MESSAGES)

      // Dispatch to topic subscribers
      const handlers = subscribers.get(msg.topic)
      if (handlers) {
        for (const handler of handlers) {
          handler(msg.data)
        }
      }
    } catch {
      // Ignore unparseable messages
    }
  }

  socket.onclose = () => {
    globalConnected.value = false
    socket = null
    if (refCount > 0) {
      scheduleReconnect()
    }
  }

  socket.onerror = () => {
    socket?.close()
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  const delay = Math.min(BASE_DELAY * 2 ** reconnectAttempt, MAX_DELAY)
  reconnectAttempt++
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connect()
  }, delay)
}

function disconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  reconnectAttempt = 0
  socket?.close()
  socket = null
  globalConnected.value = false
}

export function useWebSocket() {
  refCount++
  if (refCount === 1) {
    connect()
  }

  function subscribe(topic: string, handler: MessageHandler) {
    if (!subscribers.has(topic)) {
      subscribers.set(topic, new Set())
      // Subscribe on the socket if already connected
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: 'subscribe', topic }))
      }
    }
    subscribers.get(topic)!.add(handler)

    return () => {
      const handlers = subscribers.get(topic)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          subscribers.delete(topic)
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'unsubscribe', topic }))
          }
        }
      }
    }
  }

  onUnmounted(() => {
    refCount--
    if (refCount <= 0) {
      refCount = 0
      disconnect()
    }
  })

  return {
    connected: globalConnected,
    messages: globalMessages,
    subscribe,
  }
}
