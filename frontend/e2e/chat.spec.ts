import { test, expect } from '@playwright/test'

test.describe('Chat API', () => {
  test('GET /api/modules includes chat', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('chat')
  })

  test('GET /api/chat/health returns status', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/chat/health')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('status')
  })
})

test.describe('Chat — Navigation', () => {
  test('sidebar shows Chat nav link', async ({ page }) => {
    await page.goto('/')
    const link = page.locator('nav a', { hasText: 'Chat' })
    await expect(link).toBeVisible()
  })

  test('/chat renders without console errors', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()) })
    page.on('pageerror', (err) => errors.push(err.message))
    await page.goto('/chat')
    await page.waitForTimeout(2000)
    expect(errors.filter((e) => !e.includes('favicon'))).toHaveLength(0)
  })

  test('/chat shows message input area', async ({ page }) => {
    await page.goto('/chat')
    await expect(page.locator('textarea, input[type="text"]').first()).toBeVisible({ timeout: 5000 })
  })

  test('/chat shows send button', async ({ page }) => {
    await page.goto('/chat')
    await expect(page.locator('button').filter({ hasText: /send/i }).first()).toBeVisible({ timeout: 5000 })
  })
})
