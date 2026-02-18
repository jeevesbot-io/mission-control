import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { components } from '@/types/api'

type ContentItem = components['schemas']['ContentItem']
type ContentCreate = components['schemas']['ContentCreate']
type ContentUpdate = components['schemas']['ContentUpdate']

export const useContentStore = defineStore('content', () => {
  const items = ref<ContentItem[]>([])
  const stats = ref<Record<string, any>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPipeline() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/content/')
      if (!response.ok) {
        throw new Error(`Failed to fetch content: ${response.statusText}`)
      }
      const data = await response.json()
      items.value = data.items || []
      stats.value = data.stats || {}
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error fetching content:', e)
    } finally {
      loading.value = false
    }
  }

  async function createItem(create: ContentCreate): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/content/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(create),
      })
      if (!response.ok) {
        throw new Error(`Failed to create content: ${response.statusText}`)
      }
      await fetchPipeline()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error creating content:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  async function updateItem(itemId: string, update: ContentUpdate): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/content/${itemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      })
      if (!response.ok) {
        throw new Error(`Failed to update content: ${response.statusText}`)
      }
      await fetchPipeline()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error updating content:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  async function deleteItem(itemId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/content/${itemId}`, {
        method: 'DELETE',
      })
      if (!response.ok) {
        throw new Error(`Failed to delete content: ${response.statusText}`)
      }
      await fetchPipeline()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error deleting content:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  async function moveItem(itemId: string, targetStage: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/content/${itemId}/move/${targetStage}`, {
        method: 'POST',
      })
      if (!response.ok) {
        throw new Error(`Failed to move content: ${response.statusText}`)
      }
      await fetchPipeline()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Error moving content:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    stats,
    loading,
    error,
    fetchPipeline,
    createItem,
    updateItem,
    deleteItem,
    moveItem,
  }
})
