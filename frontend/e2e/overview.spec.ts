import { test, expect } from '@playwright/test'

test.describe('Overview Page — Enhanced', () => {
  test('shows time-aware greeting', async ({ page }) => {
    await page.goto('/')
    const greeting = page.locator('.overview__greeting')
    await expect(greeting).toBeVisible()
    const text = await greeting.textContent()
    expect(text).toMatch(/Good (morning|afternoon|evening), Commander/)
  })

  test('shows all stat cards including agents and school', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Backend Status')).toBeVisible()
    await expect(page.locator('text=Build Version')).toBeVisible()
    await expect(page.locator('text=Memory Files')).toBeVisible()
    await expect(page.locator('text=Agent Runs (24h)')).toBeVisible()
    await expect(page.locator('text=Upcoming Events')).toBeVisible()
    await expect(page.locator('text=Pending Tasks')).toBeVisible()
  })

  test('shows all three quick-access cards as live links', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('a', { hasText: 'Memory Explorer' })).toBeVisible()
    await expect(page.locator('a', { hasText: 'Agent Control' })).toBeVisible()
    await expect(page.locator('a', { hasText: 'School Dashboard' })).toBeVisible()
  })

  test('quick-access cards link to correct pages', async ({ page }) => {
    await page.goto('/')
    const agentCard = page.locator('a', { hasText: 'Agent Control' })
    await expect(agentCard).toHaveAttribute('href', '/agents')

    const schoolCard = page.locator('a', { hasText: 'School Dashboard' })
    await expect(schoolCard).toHaveAttribute('href', '/school')
  })

  test('shows activity section with widgets', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Activity')).toBeVisible()
    // Should have at least the Recent Memories widget
    await expect(page.locator('text=Recent Memories')).toBeVisible()
  })

  test('shows Agent Activity widget', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Agent Activity')).toBeVisible()
  })

  test('shows Upcoming Events widget', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Upcoming Events')).toBeVisible()
  })
})
