import { test, expect } from '@playwright/test'

test.describe('Agents Module — User Acceptance', () => {
  test('sidebar shows Agents nav link', async ({ page }) => {
    await page.goto('/')
    const agentsLink = page.locator('nav a', { hasText: 'Agents' })
    await expect(agentsLink).toBeVisible()
  })

  test('overview page shows Agent Runs stat card', async ({ page }) => {
    await page.goto('/')
    const statCard = page.locator('text=Agent Runs (24h)')
    await expect(statCard).toBeVisible()
  })

  test('overview page shows Agent Control quick-access card', async ({ page }) => {
    await page.goto('/')
    const card = page.locator('text=Agent Control')
    await expect(card).toBeVisible()
  })

  test('navigates to /agents page', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.locator('text=Agent Control')).toBeVisible()
    await expect(page.locator('text=Monitor and trigger agent runs')).toBeVisible()
  })

  test('agents page shows telemetry section', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.locator('text=Telemetry')).toBeVisible()
  })

  test('agents page shows agents section', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.locator('h3', { hasText: 'Agents' })).toBeVisible()
  })

  test('API: /api/agents/ returns agent list', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/agents/')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
  })

  test('API: /api/agents/stats returns stats', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/agents/stats')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('total_runs')
    expect(data).toHaveProperty('success_rate')
    expect(data).toHaveProperty('runs_24h')
    expect(data).toHaveProperty('unique_agents')
  })

  test('API: /api/agents/cron returns cron info', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/agents/cron')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('jobs')
    expect(Array.isArray(data.jobs)).toBe(true)
  })

  test('API: /api/modules includes agents', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('agents')
  })
})
