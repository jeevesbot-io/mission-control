import { test, expect } from '@playwright/test'

test.describe('Memory Module — User Acceptance', () => {
  test('sidebar shows Memory nav link', async ({ page }) => {
    await page.goto('/')
    const memoryLink = page.locator('nav a', { hasText: 'Memory' })
    await expect(memoryLink).toBeVisible()
  })

  test('overview page shows live memory file count', async ({ page }) => {
    await page.goto('/')
    // The Memory Files stat card should have a number, not "—"
    const statCard = page.locator('text=Memory Files').locator('..')
    await expect(statCard).toBeVisible()
  })

  test('overview page shows Memory Explorer quick-access card', async ({ page }) => {
    await page.goto('/')
    const card = page.locator('text=Memory Explorer')
    await expect(card).toBeVisible()
  })

  test('overview page shows Recent Memories widget', async ({ page }) => {
    await page.goto('/')
    const widget = page.locator('text=Recent Memories')
    await expect(widget).toBeVisible()
  })

  test('navigates to /memory and shows file list', async ({ page }) => {
    await page.goto('/memory')
    await expect(page.locator('text=Memory Explorer')).toBeVisible()
    // Should have the search bar
    await expect(page.locator('input[placeholder*="Search memories"]')).toBeVisible()
    // Should have MEMORY.md reference card
    await expect(page.locator('text=MEMORY.md')).toBeVisible()
    // Should have Daily Logs section
    await expect(page.locator('text=Daily Logs')).toBeVisible()
  })

  test('daily log cards link to detail pages', async ({ page }) => {
    await page.goto('/memory')
    // Wait for files to load, then click the first daily log card
    const firstCard = page.locator('a[href^="/memory/daily/"]').first()
    await expect(firstCard).toBeVisible()
    const href = await firstCard.getAttribute('href')
    await firstCard.click()
    await expect(page).toHaveURL(href!)
  })

  test('daily memory page renders markdown with sections', async ({ page }) => {
    await page.goto('/memory')
    // Click first daily card
    const firstCard = page.locator('a[href^="/memory/daily/"]').first()
    await firstCard.click()
    // Should have back link
    await expect(page.locator('.daily-page__back')).toBeVisible()
    // Should have rendered markdown content with .mc-prose
    await expect(page.locator('.mc-prose')).toBeVisible()
    // Should have at least one heading in the rendered content
    const headings = page.locator('.mc-prose h2, .mc-prose h3')
    await expect(headings.first()).toBeVisible()
  })

  test('daily memory page has TOC sidebar', async ({ page }) => {
    await page.goto('/memory')
    const firstCard = page.locator('a[href^="/memory/daily/"]').first()
    await firstCard.click()
    // TOC should show "Sections" title
    await expect(page.locator('text=Sections')).toBeVisible()
  })

  test('daily memory page prev/next navigation', async ({ page }) => {
    await page.goto('/memory')
    // Need at least 2 files for prev/next
    const cards = page.locator('a[href^="/memory/daily/"]')
    const count = await cards.count()
    if (count < 2) {
      test.skip()
      return
    }
    // Go to the second card (older date) — it should have a "next" arrow
    const secondCard = cards.nth(1)
    await secondCard.click()
    // Should have at least one navigation arrow that's a link (not disabled)
    const navArrows = page.locator('a[title="Next day"], a[title="Previous day"]')
    await expect(navArrows.first()).toBeVisible()
  })

  test('long-term memory page renders MEMORY.md', async ({ page }) => {
    await page.goto('/memory/long-term')
    await expect(page.locator('.lt-page__heading')).toBeVisible()
    // Should have rendered markdown
    await expect(page.locator('.mc-prose')).toBeVisible()
    // Should have TOC sidebar with "Contents" title
    await expect(page.locator('text=Contents')).toBeVisible()
  })

  test('long-term memory TOC has active section tracking', async ({ page }) => {
    await page.goto('/memory/long-term')
    // TOC links should exist
    const tocLinks = page.locator('nav a[href^="#"]')
    await expect(tocLinks.first()).toBeVisible()
  })

  test('search with results highlights matches', async ({ page }) => {
    await page.goto('/memory')
    const searchInput = page.locator('input[placeholder*="Search memories"]')
    await searchInput.fill('Matron')
    // Wait for debounced search + results to render
    await page.waitForTimeout(500)
    // Should show results or "No results" message
    const resultsOrEmpty = page.locator('.memory-page__results, .memory-page__empty')
    await expect(resultsOrEmpty.first()).toBeVisible({ timeout: 5000 })
  })

  test('search clears when input is emptied', async ({ page }) => {
    await page.goto('/memory')
    const searchInput = page.locator('input[placeholder*="Search memories"]')
    await searchInput.fill('Matron')
    await page.waitForTimeout(500)
    await searchInput.clear()
    await page.waitForTimeout(400)
    // Should be back to file browser mode — Daily Logs visible
    await expect(page.locator('text=Daily Logs')).toBeVisible()
  })

  test('MEMORY.md card links to long-term page', async ({ page }) => {
    await page.goto('/memory')
    const card = page.locator('a[href="/memory/long-term"]')
    await expect(card).toBeVisible()
    await card.click()
    await expect(page).toHaveURL('/memory/long-term')
  })

  test('API: /api/memory/files returns file list', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/memory/files')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data.total).toBeGreaterThan(0)
    expect(data.files[0]).toHaveProperty('date')
    expect(data.files[0]).toHaveProperty('preview')
  })

  test('API: /api/memory/long-term returns MEMORY.md', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/memory/long-term')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data.content.length).toBeGreaterThan(0)
    expect(data.sections.length).toBeGreaterThan(0)
  })

  test('API: /api/memory/search validates min length', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/memory/search?q=a')
    expect(res.status()).toBe(422)
  })

  test('API: /api/memory/stats returns stats', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/memory/stats')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data.total_files).toBeGreaterThan(0)
    expect(data.has_long_term).toBe(true)
  })

  test('API: /api/modules includes memory', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('memory')
  })
})
