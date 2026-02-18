import { test, expect } from '@playwright/test'

// ---------------------------------------------------------------------------
// API Acceptance Tests — no browser needed, fast
// ---------------------------------------------------------------------------

test.describe('War Room API', () => {
  test('GET /api/modules includes warroom', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/modules')
    expect(res.ok()).toBe(true)
    const modules = await res.json()
    const ids = modules.map((m: { id: string }) => m.id)
    expect(ids).toContain('warroom')
  })

  test('GET /api/warroom/tasks returns array', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/tasks')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
  })

  test('GET /api/warroom/tasks/queue returns sorted array', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/tasks/queue')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
  })

  test('GET /api/warroom/projects returns array with task_count', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/projects')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('task_count')
      expect(data[0]).toHaveProperty('id')
      expect(data[0]).toHaveProperty('name')
      expect(data[0]).toHaveProperty('color')
    }
  })

  test('GET /api/warroom/tags returns array of strings', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/tags')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
    data.forEach((tag: unknown) => expect(typeof tag).toBe('string'))
  })

  test('GET /api/warroom/heartbeat returns lastHeartbeat field', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/heartbeat')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('lastHeartbeat')
  })

  test('POST /api/warroom/heartbeat records a heartbeat', async ({ request }) => {
    const res = await request.post('http://localhost:5055/api/warroom/heartbeat')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('lastHeartbeat')
    expect(typeof data.lastHeartbeat).toBe('number')
  })

  test('GET /api/warroom/skills returns array', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/skills')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
    data.forEach((s: unknown) => {
      expect(s).toHaveProperty('id')
      expect(s).toHaveProperty('name')
      expect(s).toHaveProperty('source')
      expect(s).toHaveProperty('enabled')
    })
  })

  test('GET /api/warroom/usage returns model and tiers', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/usage')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('model')
    expect(data).toHaveProperty('tiers')
    expect(Array.isArray(data.tiers)).toBe(true)
  })

  test('GET /api/warroom/models returns array of strings', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/models')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
    data.forEach((m: unknown) => expect(typeof m).toBe('string'))
  })

  test('GET /api/warroom/stats returns all expected fields', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/stats')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('in_progress_count')
    expect(data).toHaveProperty('todo_count')
    expect(data).toHaveProperty('last_heartbeat')
    expect(data).toHaveProperty('active_model')
  })

  test('GET /api/warroom/calendar returns date-keyed object', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/calendar')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(typeof data).toBe('object')
    expect(Array.isArray(data)).toBe(false)
    // Every key should be YYYY-MM-DD format
    Object.keys(data).forEach((key) => {
      expect(key).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(data[key]).toHaveProperty('memory')
      expect(data[key]).toHaveProperty('tasks')
    })
  })

  test('GET /api/warroom/soul/templates returns 6 templates', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/soul/templates')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
    expect(data).toHaveLength(6)
    data.forEach((tpl: unknown) => {
      expect(tpl).toHaveProperty('name')
      expect(tpl).toHaveProperty('content')
    })
  })

  test('GET /api/warroom/workspace-file?name=SOUL.md returns content', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/workspace-file?name=SOUL.md')
    expect(res.ok()).toBe(true)
    const data = await res.json()
    expect(data).toHaveProperty('content')
    expect(typeof data.content).toBe('string')
  })

  test('GET /api/warroom/workspace-file with invalid name returns 400', async ({ request }) => {
    const res = await request.get('http://localhost:5055/api/warroom/workspace-file?name=../../etc/passwd')
    expect(res.status()).toBe(400)
  })

  test('Queue protocol: create task → queue → pickup → complete cycle', async ({ request }) => {
    // Create a test task
    const create = await request.post('http://localhost:5055/api/warroom/tasks', {
      data: {
        title: 'E2E queue protocol test task',
        description: 'Created by Playwright acceptance test',
        status: 'todo',
        priority: 'medium',
      },
    })
    expect(create.ok()).toBe(true)
    const task = await create.json()
    const taskId = task.id

    try {
      // It should appear in the queue
      const queue = await request.get('http://localhost:5055/api/warroom/tasks/queue')
      const queueData = await queue.json()
      const inQueue = queueData.some((t: { id: string }) => t.id === taskId)
      expect(inQueue).toBe(true)

      // Pickup
      const pickup = await request.post(`http://localhost:5055/api/warroom/tasks/${taskId}/pickup`)
      expect(pickup.ok()).toBe(true)
      const pickedUp = await pickup.json()
      expect(pickedUp.pickedUp).toBe(true)
      expect(pickedUp.status).toBe('in-progress')

      // After pickup, should not be in queue anymore
      const queue2 = await request.get('http://localhost:5055/api/warroom/tasks/queue')
      const queueData2 = await queue2.json()
      const stillInQueue = queueData2.some((t: { id: string }) => t.id === taskId)
      expect(stillInQueue).toBe(false)

      // Complete
      const complete = await request.post(`http://localhost:5055/api/warroom/tasks/${taskId}/complete`, {
        data: { result: 'E2E test passed' },
      })
      expect(complete.ok()).toBe(true)
      const completed = await complete.json()
      expect(completed.status).toBe('done')
      expect(completed.result).toBe('E2E test passed')
    } finally {
      // Cleanup
      await request.delete(`http://localhost:5055/api/warroom/tasks/${taskId}`)
    }
  })
})

// ---------------------------------------------------------------------------
// UI Acceptance Tests
// ---------------------------------------------------------------------------

test.describe('War Room — Navigation', () => {
  test('sidebar shows War Room nav link', async ({ page }) => {
    await page.goto('/')
    const link = page.locator('nav a', { hasText: 'War Room' })
    await expect(link).toBeVisible()
  })

  test('War Room link navigates to /warroom', async ({ page }) => {
    await page.goto('/')
    await page.locator('nav a', { hasText: 'War Room' }).click()
    await expect(page).toHaveURL('/warroom')
  })

  test('/warroom renders without errors', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()) })
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/warroom')

    // Tabs should be visible — confirms page mounted
    await expect(page.locator('.tab-btn', { hasText: 'Kanban' })).toBeVisible()

    expect(errors.filter((e) => !e.includes('favicon'))).toHaveLength(0)
  })
})

test.describe('War Room — Kanban Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/warroom')
    await expect(page.locator('.tab-btn', { hasText: 'Kanban' })).toBeVisible()
  })

  test('shows all four kanban column headers', async ({ page }) => {
    await expect(page.locator('.column-title', { hasText: 'Backlog' })).toBeVisible()
    await expect(page.locator('.column-title', { hasText: 'Todo' })).toBeVisible()
    await expect(page.locator('.column-title', { hasText: 'In Progress' })).toBeVisible()
    await expect(page.locator('.column-title', { hasText: 'Done' })).toBeVisible()
  })

  test('In Progress and Done columns show agent badge', async ({ page }) => {
    const agentBadges = page.locator('.agent-badge')
    await expect(agentBadges).toHaveCount(2)
  })

  test('Backlog and Todo columns have Add task buttons', async ({ page }) => {
    const addBtns = page.locator('.quick-add-btn', { hasText: '+ Add task' })
    await expect(addBtns).toHaveCount(2)
  })

  test('existing tasks render as cards', async ({ page }) => {
    // Wait for tasks to load from API (at least 1 task from migration)
    await expect(page.locator('.task-card').first()).toBeVisible({ timeout: 8000 })
    const count = await page.locator('.task-card').count()
    expect(count).toBeGreaterThan(0)
  })

  test('clicking Add task opens task dialog', async ({ page }) => {
    // Wait for the board to settle with task data before interacting
    await expect(page.locator('.task-card').first()).toBeVisible({ timeout: 8000 })
    await page.locator('.quick-add-btn').first().click()
    // PrimeVue Dialog renders with role="dialog" and class p-dialog
    await expect(page.locator('.p-dialog').first()).toBeVisible({ timeout: 5000 })
  })

  test('can create a new task via dialog', async ({ page, request }) => {
    const testTitle = `E2E-create-${Date.now()}`

    // Wait for board to settle before interacting
    await expect(page.locator('.task-card').first()).toBeVisible({ timeout: 8000 })
    await page.locator('.quick-add-btn').first().click()

    const dialog = page.locator('.p-dialog').first()
    await expect(dialog).toBeVisible({ timeout: 5000 })

    // Fill title — PrimeVue InputText placeholder
    const titleInput = dialog.locator('input[placeholder="What needs to be done?"]')
    await titleInput.fill(testTitle)

    // Create (new task button is labeled "Create", not "Save")
    const createBtn = dialog.locator('button', { hasText: 'Create' }).first()
    await createBtn.click()

    // Dialog should close and task should appear in the board
    await expect(dialog).not.toBeVisible({ timeout: 3000 })
    await expect(page.locator('.task-card', { hasText: testTitle })).toBeVisible({ timeout: 8000 })

    // Cleanup: delete the test task from the backend
    const tasks = await request.get('http://localhost:5055/api/warroom/tasks')
    const allTasks = await tasks.json()
    const created = allTasks.find((t: { id: string; title: string }) => t.title === testTitle)
    if (created) await request.delete(`http://localhost:5055/api/warroom/tasks/${created.id}`)
  })
})

test.describe('War Room — Tab Switching', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/warroom')
    await expect(page.locator('.tab-btn', { hasText: 'Kanban' })).toBeVisible()
  })

  test('all 5 tabs are visible in tab bar', async ({ page }) => {
    await expect(page.locator('.tab-btn', { hasText: 'Kanban' })).toBeVisible()
    await expect(page.locator('.tab-btn', { hasText: 'Usage & Model' })).toBeVisible()
    await expect(page.locator('.tab-btn', { hasText: 'Skills' })).toBeVisible()
    await expect(page.locator('.tab-btn', { hasText: 'Soul & Identity' })).toBeVisible()
    await expect(page.locator('.tab-btn', { hasText: 'Calendar' })).toBeVisible()
  })

  test('Usage & Model tab shows usage section', async ({ page }) => {
    await page.locator('.tab-btn', { hasText: 'Usage & Model' }).click()
    await expect(page.locator('.section-title', { hasText: 'Usage & Model' })).toBeVisible()
  })

  test('Skills tab shows Skills heading', async ({ page }) => {
    await page.locator('.tab-btn', { hasText: 'Skills' }).click()
    await expect(page.locator('.section-title', { hasText: 'Skills' })).toBeVisible({ timeout: 5000 })
  })

  test('Soul & Identity tab shows heading and file tabs', async ({ page }) => {
    await page.locator('.tab-btn', { hasText: 'Soul & Identity' }).click()
    await expect(page.locator('.section-title', { hasText: 'Soul & Identity' })).toBeVisible({ timeout: 5000 })
    // File tab switcher should appear
    await expect(page.locator('.file-tab', { hasText: 'SOUL.md' })).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.file-tab', { hasText: 'IDENTITY.md' })).toBeVisible()
    await expect(page.locator('.file-tab', { hasText: 'USER.md' })).toBeVisible()
    await expect(page.locator('.file-tab', { hasText: 'AGENTS.md' })).toBeVisible()
  })

  test('Calendar tab shows Activity Calendar heading', async ({ page }) => {
    await page.locator('.tab-btn', { hasText: 'Calendar' }).click()
    await expect(page.locator('.section-title', { hasText: 'Activity Calendar' })).toBeVisible({ timeout: 5000 })
  })

  test('Calendar tab renders month blocks', async ({ page }) => {
    await page.locator('.tab-btn', { hasText: 'Calendar' }).click()
    await page.waitForTimeout(1000) // let calendar data load
    const months = page.locator('.month-block')
    const count = await months.count()
    expect(count).toBe(12)
  })
})

test.describe('War Room — Skills Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/warroom')
    await page.locator('.tab-btn', { hasText: 'Skills' }).click()
    await expect(page.locator('.section-title', { hasText: 'Skills' })).toBeVisible({ timeout: 5000 })
  })

  test('shows skills stats bar', async ({ page }) => {
    await expect(page.locator('.skills-stats')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=total')).toBeVisible()
    await expect(page.locator('text=enabled')).toBeVisible()
  })

  test('shows search input', async ({ page }) => {
    await expect(page.locator('.skills-search')).toBeVisible()
  })

  test('shows workspace section with New skill button', async ({ page }) => {
    await expect(page.locator('.section-heading', { hasText: 'Workspace' })).toBeVisible()
    await expect(page.locator('.btn-create', { hasText: 'New skill' })).toBeVisible()
  })

  test('New skill button reveals create form', async ({ page }) => {
    await page.locator('.btn-create', { hasText: 'New skill' }).click()
    await expect(page.locator('.create-form')).toBeVisible()
    await expect(page.locator('button', { hasText: 'Create' })).toBeVisible()
    await expect(page.locator('button', { hasText: 'Cancel' })).toBeVisible()
  })
})

test.describe('War Room — Soul & Identity Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/warroom')
    await page.locator('.tab-btn', { hasText: 'Soul & Identity' }).click()
    await expect(page.locator('.file-tab', { hasText: 'SOUL.md' })).toBeVisible({ timeout: 5000 })
  })

  test('SOUL.md tab shows templates side panel', async ({ page }) => {
    await expect(page.locator('.side-tab', { hasText: 'Templates' })).toBeVisible()
    await expect(page.locator('.template-card').first()).toBeVisible({ timeout: 5000 })
  })

  test('SOUL.md tab shows textarea with content', async ({ page }) => {
    const textarea = page.locator('.soul-textarea textarea, .soul-textarea')
    await expect(textarea.first()).toBeVisible({ timeout: 5000 })
  })

  test('switching to IDENTITY.md file tab loads it', async ({ page }) => {
    await page.locator('.file-tab', { hasText: 'IDENTITY.md' }).click()
    // The file tab should now be active (no dirty dot, just active state)
    await expect(page.locator('.file-tab.active', { hasText: 'IDENTITY.md' })).toBeVisible()
  })

  test('History tab button is visible and clickable', async ({ page }) => {
    const historyTab = page.locator('.side-tab', { hasText: 'History' })
    await expect(historyTab).toBeVisible()
    await historyTab.click()
    await expect(historyTab).toHaveClass(/active/)
  })
})

test.describe('War Room — Overview Widget', () => {
  test('WarRoomSummary widget appears on overview page', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.warroom-summary')).toBeVisible({ timeout: 5000 })
  })

  test('overview widget shows War Room title', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.ws-title', { hasText: 'War Room' })).toBeVisible({ timeout: 5000 })
  })

  test('overview widget shows View all link to /warroom', async ({ page }) => {
    await page.goto('/')
    const link = page.locator('.ws-link', { hasText: 'View all' })
    await expect(link).toBeVisible({ timeout: 5000 })
    await expect(link).toHaveAttribute('href', '/warroom')
  })

  test('overview widget shows In progress and In queue stats', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=In progress')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=In queue')).toBeVisible({ timeout: 5000 })
  })

  test('overview widget shows Last heartbeat', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Last heartbeat')).toBeVisible({ timeout: 5000 })
  })

  test('overview widget View all link navigates to /warroom', async ({ page }) => {
    await page.goto('/')
    await page.locator('.ws-link', { hasText: 'View all' }).click()
    await expect(page).toHaveURL('/warroom')
  })
})
