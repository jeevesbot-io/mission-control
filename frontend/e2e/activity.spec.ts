import { test, expect } from '@playwright/test'

test.describe('Activity API', () => {
  test('GET /api/modules includes activity', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('activity')
  })

  test('GET /api/activity/feed returns events and total', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/activity/feed')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('events')
    expect(data).toHaveProperty('total')
    expect(Array.isArray(data.events)).toBe(true)
  })

  test('GET /api/activity/feed accepts filters', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/activity/feed?module=warroom&limit=10')
    expect(res.ok()).toBe(true)
  })

  test('GET /api/activity/stats returns stats', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/activity/stats')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('total_events')
    expect(data).toHaveProperty('by_module')
    expect(data).toHaveProperty('by_actor')
    expect(data).toHaveProperty('last_24h')
  })
})

test.describe('Activity — Navigation', () => {
  test('sidebar shows Activity nav link', async ({ page }) => {
    await page.goto('/')
    const link = page.locator('nav a', { hasText: 'Activity' })
    await expect(link).toBeVisible()
  })

  test('/activity renders without console errors', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()) })
    page.on('pageerror', (err) => errors.push(err.message))
    await page.goto('/activity')
    await page.waitForTimeout(2000)
    expect(errors.filter((e) => !e.includes('favicon'))).toHaveLength(0)
  })

  test('/activity shows Activity Timeline title', async ({ page }) => {
    await page.goto('/activity')
    await expect(page.locator('text=Activity Timeline')).toBeVisible({ timeout: 5000 })
  })

  test('/activity shows module filter buttons', async ({ page }) => {
    await page.goto('/activity')
    await expect(page.locator('.activity__filter-btn', { hasText: 'All' })).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.activity__filter-btn', { hasText: 'War Room' })).toBeVisible()
  })

  test('/activity shows stats section', async ({ page }) => {
    await page.goto('/activity')
    await expect(page.locator('text=Overview')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Total Events')).toBeVisible()
  })
})
