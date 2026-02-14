---
tags: [jeevesbot, mission-control, modules]
date created: 2026-02-13
date modified: 2026-02-13
title: Mission Control — Module Registry
---

# Module Registry

Every domain in Mission Control is a self-contained module with a backend router (FastAPI) and frontend views (Vue 3). Modules auto-register via a standard `MODULE_INFO` definition.

---

## Active Modules (all live)

### 🏠 Overview (`navOrder: 0`)
- **Purpose:** Landing page and unified dashboard. Aggregates data from all modules via a single `/api/overview` endpoint.
- **Backend:** `GET /api/overview` — returns health status, stats (agents active, events this week, emails processed, tasks pending), upcoming events (7 days from Google Calendar), recent agent activity (last 10 log entries), system health (DB, uptime, version)
- **Frontend:** Stat cards, upcoming events list (colour-coded by child), recent agent activity feed, system health indicators, WebSocket subscription + 30s auto-refresh
- **Data sources:** Aggregates from `agent_log`, Google Calendar (via gog CLI), `school_emails`, `todoist_tasks` tables + system health checks
- **Key views:** Overview dashboard with two-column layout (events + activity)

### 📜 Memory (`navOrder: 1`)
- **Purpose:** Browse, search, and inspect Jeeves' memory system
- **Backend:** `GET /api/memory/files`, `/files/{date}`, `/long-term`, `/search?q=`, `/stats`
- **Frontend:** Memory explorer, full-text search with highlighted snippets, MEMORY.md viewer with TOC sidebar, daily file browser, prev/next navigation
- **Data sources:** Markdown files (`memory/*.md`, `MEMORY.md`) via direct file read. Full-text search in-process; files are source of truth, cached in-memory with mtime invalidation.
- **Agent:** [[Archivist - MOC|The Archivist 📜]]
- **Overview widget:** Recent memories (top 3 files)
- **Tests:** 8 backend integration tests, 9 frontend store tests, 28 Playwright e2e tests

### ⚡ Agents (`navOrder: 2`)
- **Purpose:** Agent monitoring, log history, cron schedule, manual triggers, live activity feed
- **Backend:** `GET /api/agents/`, `/stats`, `/{id}/log`, `/cron`, `POST /{id}/trigger`
- **Frontend:** Agent cards grid with level badges (info/warning/error), log history table (paginated, filterable by level), cron schedule, trigger buttons, live WebSocket activity feed
- **Data sources:** Postgres (`agent_log` — serial PK, JSONB metadata, `agent` column for agent ID), OpenClaw gateway API (`:18789`) for cron status + trigger execution
- **WebSocket:** Trigger events broadcast on `agents:activity` topic
- **Overview widget:** Agent activity (recent log entries with level icons)
- **Tests:** 12 backend integration tests, 12 frontend store tests, Playwright e2e suite

### 🏥 School (`navOrder: 3`)
- **Purpose:** Family calendar, school emails, tasks (Matron's domain, now in Mission Control)
- **Backend:** `GET /api/school/calendar` (Google Calendar via gog CLI), `/events`, `/emails`, `/tasks`, `/stats`
- **Frontend:** Tabbed view (Calendar | Emails | Tasks) with stat cards, child colour bars (Natty=blue, Elodie=purple, Florence=green), child inference from event summaries
- **Data sources:** Google Calendar via `gog` CLI subprocess (`sollyfamily3@gmail.com` account), Postgres (`school_emails`, `school_events`, `todoist_tasks`) via raw SQL. Graceful degradation if tables don't exist or gog times out.
- **Agent:** [[Matron - MOC|Matron 🏥]]
- **Overview widget:** Upcoming events (next 5)
- **Tests:** 10 backend integration tests, 8 frontend store tests, Playwright e2e suite

### 📊 Analytics (planned)
- **Purpose:** Trends and patterns across all modules
- **Data sources:** All module APIs, aggregated
- **Key views:** Memory growth, agent activity, email processing trends
- **Overview widget:** Sparkline charts

---

## Planned Modules (Future)

| Module | Icon | Purpose | Likely Data Source |
|--------|------|---------|-------------------|
| Health | ❤️ | Health tracking, metrics, habits | TBD (Apple Health? Manual?) |
| Finance | 💰 | Spending, budgets, financial overview | TBD (Monzo API? CSV import?) |
| Reading | 📚 | Reading list, progress, notes | Obsidian notes? Kindle? |
| Dog Training | 🐕 | Training log, progress, reminders | Manual input / Todoist? |
| Weather | 🌤️ | Forecast, commute impact | Weather API |
| Calendar | 📅 | Unified calendar view | Google Calendar API |

---

## Module Contract

Every module must provide:

### Backend (`backend/modules/<name>/`)
```python
# __init__.py
MODULE_INFO = {
    "id": "module_name",        # unique identifier
    "name": "Display Name",     # human-readable
    "icon": "🔮",               # emoji for nav
    "router": router,           # FastAPI APIRouter instance
    "prefix": "/api/module",    # API path prefix
}
```

### Frontend (`frontend/src/modules/<name>/`)
```typescript
// routes.ts
export default {
  module: {
    id: 'module_name',
    name: 'Display Name',
    icon: '🔮',
    navOrder: 10,               // sidebar position
  },
  routes: [
    { path: '/module', component: () => import('./ModulePage.vue') },
  ],
  overviewWidgets: [
    () => import('./widgets/SummaryWidget.vue'),
  ],
}
```

Both are auto-discovered by the core registry. No editing core files to add a module.
