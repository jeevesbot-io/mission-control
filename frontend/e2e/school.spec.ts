import { test, expect } from '@playwright/test'

test.describe('School Module — User Acceptance', () => {
  test('sidebar shows School nav link', async ({ page }) => {
    await page.goto('/')
    const schoolLink = page.locator('nav a', { hasText: 'School' })
    await expect(schoolLink).toBeVisible()
  })

  test('overview page shows School Dashboard quick-access card', async ({ page }) => {
    await page.goto('/')
    const card = page.locator('text=School Dashboard')
    await expect(card).toBeVisible()
  })

  test('overview page shows Upcoming Events stat card', async ({ page }) => {
    await page.goto('/')
    const statCard = page.locator('text=Upcoming Events')
    await expect(statCard).toBeVisible()
  })

  test('overview page shows Pending Tasks stat card', async ({ page }) => {
    await page.goto('/')
    const statCard = page.locator('text=Pending Tasks')
    await expect(statCard).toBeVisible()
  })

  test('navigates to /school page', async ({ page }) => {
    await page.goto('/school')
    await expect(page.locator('text=School Dashboard')).toBeVisible()
    await expect(page.locator('text=Events, emails, and tasks in one place')).toBeVisible()
  })

  test('school page has three tabs', async ({ page }) => {
    await page.goto('/school')
    await expect(page.locator('button', { hasText: 'Events' })).toBeVisible()
    await expect(page.locator('button', { hasText: 'Emails' })).toBeVisible()
    await expect(page.locator('button', { hasText: 'Tasks' })).toBeVisible()
  })

  test('school page tabs switch content', async ({ page }) => {
    await page.goto('/school')
    // Click Emails tab
    await page.locator('button', { hasText: 'Emails' }).click()
    // Events tab should no longer be active
    const emailsTab = page.locator('button', { hasText: 'Emails' })
    await expect(emailsTab).toHaveClass(/school__tab--active/)
  })

  test('API: /api/school/events returns events', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/school/events')
    // May return 200 even if table doesn't exist (graceful degradation)
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('events')
    expect(data).toHaveProperty('total')
  })

  test('API: /api/school/emails returns emails', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/school/emails')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('emails')
    expect(data).toHaveProperty('total')
  })

  test('API: /api/school/tasks returns tasks', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/school/tasks')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('tasks')
    expect(data).toHaveProperty('total')
  })

  test('API: /api/school/stats returns stats', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/school/stats')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('upcoming_events')
    expect(data).toHaveProperty('unread_emails')
    expect(data).toHaveProperty('pending_tasks')
    expect(data).toHaveProperty('completed_today')
  })

  test('API: /api/modules includes school', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('school')
  })
})
