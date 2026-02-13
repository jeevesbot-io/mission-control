import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from './app'

describe('app store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('defaults to dark mode', () => {
    const store = useAppStore()
    expect(store.darkMode).toBe(true)
  })

  it('toggles dark mode', () => {
    const store = useAppStore()
    store.toggleDarkMode()
    expect(store.darkMode).toBe(false)
  })

  it('toggles sidebar', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
  })
})
