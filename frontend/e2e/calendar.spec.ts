import { test, expect } from '@playwright/test'

test.describe('Calendar API', () => {
  test('GET /api/modules includes calendar', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('calendar')
  })

  test('GET /api/calendar returns events array', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/calendar/')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('events')
    expect(Array.isArray(data.events)).toBe(true)
  })

  test('GET /api/calendar accepts days_ahead param', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/calendar/?days_ahead=7')
    expect(res.ok()).toBe(true)
  })

  test('GET /api/calendar/jobs returns cron jobs', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/calendar/jobs')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
  })
})

test.describe('Calendar — Navigation', () => {
  test('sidebar shows Calendar nav link', async ({ page }) => {
    await page.goto('/')
    const link = page.locator('nav a', { hasText: 'Calendar' })
    await expect(link).toBeVisible()
  })

  test('/calendar renders without console errors', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()) })
    page.on('pageerror', (err) => errors.push(err.message))
    await page.goto('/calendar')
    await page.waitForTimeout(2000)
    expect(errors.filter((e) => !e.includes('favicon'))).toHaveLength(0)
  })

  test('Calendar shows view mode buttons', async ({ page }) => {
    await page.goto('/calendar')
    await expect(page.locator('text=Timeline')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Grid')).toBeVisible()
    await expect(page.locator('text=Week')).toBeVisible()
  })

  test('Calendar shows time range dropdown', async ({ page }) => {
    await page.goto('/calendar')
    await expect(page.locator('text=14 days')).toBeVisible({ timeout: 5000 })
  })
})
