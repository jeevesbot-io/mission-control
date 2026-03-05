import { test, expect } from '@playwright/test'

test.describe('Content API', () => {
  test('GET /api/modules includes content', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('content')
  })

  test('GET /api/content returns items and stats', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/content/')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('items')
    expect(data).toHaveProperty('stats')
    expect(Array.isArray(data.items)).toBe(true)
  })

  test('POST /api/content creates an item', async ({ request }) => {
    const res = await request.post('http://localhost:5055/api/content/', {
      data: { title: 'E2E test content', type: 'video', priority: 'medium' },
    })
    expect(res.ok()).toBe(true)
    const item = await res.json()
    expect(item).toHaveProperty('id')
    expect(item.title).toBe('E2E test content')
    expect(item.stage).toBe('ideas')
    // Cleanup
    await request.delete(`http://localhost:5055/api/content/${item.id}`)
  })

  test('DELETE /api/content/:id removes item', async ({ request }) => {
    const create = await request.post('http://localhost:5055/api/content/', {
      data: { title: 'E2E delete test', type: 'article' },
    })
    const item = await create.json()
    const del = await request.delete(`http://localhost:5055/api/content/${item.id}`)
    expect(del.ok()).toBe(true)
  })
})

test.describe('Content — Navigation', () => {
  test('sidebar shows Content nav link', async ({ page }) => {
    await page.goto('/')
    const link = page.locator('nav a', { hasText: 'Content' })
    await expect(link).toBeVisible()
  })

  test('/content renders kanban columns', async ({ page }) => {
    await page.goto('/content')
    await expect(page.locator('.column-title', { hasText: 'Ideas' })).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.column-title', { hasText: 'Published' })).toBeVisible()
  })

  test('/content shows New Content button', async ({ page }) => {
    await page.goto('/content')
    await expect(page.locator('button', { hasText: 'New Content' })).toBeVisible({ timeout: 5000 })
  })

  test('clicking New Content opens dialog', async ({ page }) => {
    await page.goto('/content')
    await page.locator('button', { hasText: 'New Content' }).click()
    await expect(page.locator('.p-dialog').first()).toBeVisible({ timeout: 5000 })
  })
})
