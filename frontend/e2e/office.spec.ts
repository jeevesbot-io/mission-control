import { test, expect } from '@playwright/test'

test.describe('Office API', () => {
  test('GET /api/modules includes office', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('office')
  })

  test('GET /api/office returns workstations and stats', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/office/')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('workstations')
    expect(data).toHaveProperty('office_stats')
    expect(Array.isArray(data.workstations)).toBe(true)
  })

  test('workstations have required fields', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/office/')
    const data = await res.json()
    if (data.workstations.length > 0) {
      const ws = data.workstations[0]
      expect(ws).toHaveProperty('agent_id')
      expect(ws).toHaveProperty('display_name')
      expect(ws).toHaveProperty('avatar_color')
      expect(ws).toHaveProperty('status')
      expect(ws).toHaveProperty('position')
    }
  })
})

test.describe('Office — Navigation', () => {
  test('sidebar shows Office View nav link', async ({ page }) => {
    await page.goto('/')
    const link = page.locator('nav a', { hasText: 'Office' })
    await expect(link).toBeVisible()
  })

  test('/office renders without console errors', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()) })
    page.on('pageerror', (err) => errors.push(err.message))
    await page.goto('/office')
    await page.waitForTimeout(2000)
    expect(errors.filter((e) => !e.includes('favicon'))).toHaveLength(0)
  })

  test('/office shows stats bar', async ({ page }) => {
    await page.goto('/office')
    await expect(page.locator('text=Total Agents')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Working')).toBeVisible()
    await expect(page.locator('text=Idle')).toBeVisible()
  })

  test('/office shows Digital Office panel', async ({ page }) => {
    await page.goto('/office')
    await expect(page.locator('text=Digital Office')).toBeVisible({ timeout: 5000 })
  })

  test('/office shows Team Directory panel', async ({ page }) => {
    await page.goto('/office')
    await expect(page.locator('text=Team Directory')).toBeVisible({ timeout: 5000 })
  })
})
