import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import { useAppStore } from './app'

const storage = new Map<string, string>()

beforeEach(() => {
  storage.clear()
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => storage.set(key, value),
    removeItem: (key: string) => storage.delete(key),
    clear: () => storage.clear(),
    get length() { return storage.size },
    key: (index: number) => [...storage.keys()][index] ?? null,
  })
})

describe('app store', () => {
  beforeEach(() => {
    storage.clear()
    setActivePinia(createPinia())
  })

  it('defaults to dark mode when localStorage is empty', () => {
    const store = useAppStore()
    expect(store.darkMode).toBe(true)
  })

  it('defaults sidebar expanded when localStorage is empty', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('reads darkMode from localStorage', () => {
    storage.set('mc-dark-mode', 'false')
    setActivePinia(createPinia())
    const store = useAppStore()
    expect(store.darkMode).toBe(false)
  })

  it('reads sidebarCollapsed from localStorage', () => {
    storage.set('mc-sidebar-collapsed', 'true')
    setActivePinia(createPinia())
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(true)
  })

  it('toggles dark mode and persists', async () => {
    const store = useAppStore()
    store.toggleDarkMode()
    expect(store.darkMode).toBe(false)
    await nextTick()
    expect(storage.get('mc-dark-mode')).toBe('false')
  })

  it('toggles sidebar and persists', async () => {
    const store = useAppStore()
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
    await nextTick()
    expect(storage.get('mc-sidebar-collapsed')).toBe('true')
  })
})
