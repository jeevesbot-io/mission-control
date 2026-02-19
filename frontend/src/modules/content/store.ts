import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import type { components } from '@/types/api'

type ContentItem = components['schemas']['ContentItem']
type ContentCreate = components['schemas']['ContentCreate']
type ContentUpdate = components['schemas']['ContentUpdate']

export const useContentStore = defineStore('content', () => {
  const api = useApi()
  const items = ref<ContentItem[]>([])
  const stats = ref<Record<string, any>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPipeline() {
    loading.value = true
    error.value = null
    try {
      const data = await api.get<{ items: ContentItem[]; stats: Record<string, any> }>('/api/content/')
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
      await api.post('/api/content/', create)
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
      await api.patch(`/api/content/${itemId}`, update)
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
      await api.delete(`/api/content/${itemId}`)
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
      await api.post(`/api/content/${itemId}/move/${targetStage}`)
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
