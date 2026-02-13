---
tags: [jeevesbot, mission-control, modules]
date created: 2026-02-13
date modified: 2026-02-13
title: Mission Control — Module Registry
---

# Module Registry

Every domain in Mission Control is a self-contained module with a backend router (FastAPI) and frontend views (Vue 3). Modules auto-register via a standard `MODULE_INFO` definition.

---

## Active Modules (Phase 1)

### 🏠 Overview
- **Purpose:** Landing page. Assembles widgets from all registered modules.
- **Data sources:** All module APIs
- **Key views:** Stats bar, agent status, live activity timeline, module widgets

### 📜 Memory
- **Purpose:** Browse, search, and inspect Jeeves' memory system
- **Data sources:** Markdown files (`memory/*.md`, `MEMORY.md`) via direct file read (Docker volume mount). Full-text search in-process; no separate index table — files are the source of truth, cached in-memory with file watcher invalidation.
- **Key views:** Memory explorer, full-text search, MEMORY.md viewer with section nav, daily file browser
- **Agent:** [[Archivist - MOC|The Archivist 📜]]
- **Overview widget:** Recent memories
- **Build order:** Phase 3 (first module — the killer feature)

### 🏥 School
- **Purpose:** School events, emails, tasks, calendar invites (Matron's domain)
- **Data sources:** Postgres (`school_emails`, `school_events`, `todoist_tasks`)
- **Key views:** Today/week/upcoming events, email list, action items, stats
- **Agent:** [[Matron - MOC|Matron 🏥]]
- **Overview widget:** Today's school events

### 🤖 Agents
- **Purpose:** Agent monitoring, run history, cron schedule, manual triggers
- **Data sources:** Postgres (`agent_runs` — unified table, JSONB metadata for agent-specific fields), OpenClaw gateway API (`:18789`) for cron status + trigger execution
- **Key views:** Agent status cards, run history table (paginated, filterable), cron schedule, trigger buttons
- **Overview widget:** Agent status + next scheduled run

### 📊 Analytics (stretch)
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
