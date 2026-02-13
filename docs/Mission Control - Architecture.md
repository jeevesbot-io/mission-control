---
tags: [jeevesbot, mission-control, architecture]
date created: 2026-02-13
date modified: 2026-02-13
title: Mission Control — Architecture
---

# Mission Control — Architecture

A unified dashboard and life operating system. Plugin-based architecture where each life domain (agents, memory, school, health, finance, etc.) is a self-contained module.

Replaces Matron's standalone Flask dashboard with a proper platform. Matron's views become the School module — same data, better home.

---

## Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Backend** | FastAPI (Python) | Async-native, API-first by design, Pydantic validation, WebSocket support |
| **Frontend** | Vue 3 + Vite (TypeScript) | Component-based, plugin-friendly, lighter than React, single-file components |
| **State** | Pinia | Simple, type-safe state management for Vue 3 |
| **Data** | Postgres (`jeeves` DB) | Already has Matron's tables, add unified agent + memory tables |
| **Memory data** | Markdown files (read via API) | Memory files are the source of truth, served by FastAPI |
| **Real-time** | WebSocket (`/ws/live`) | Live agent activity feeds, status updates |
| **Deployment** | Docker via Colima | Replace `matron-dashboard` container |
| **Auth** | Session cookies (signed, httpOnly) | Simple, secure for SPA, no token refresh logic. Upgrade to OAuth later if needed |
| **Migrations** | Alembic | Schema versioning, auto-generated migration scripts |
| **UI components** | PrimeVue | Provides DataTable, Modal, tabs, etc. — customise the dark theme rather than building from scratch |
| **Charts** | Apache ECharts (vue-echarts) | Lightweight, good defaults, handles sparklines through to full dashboards |
| **Type generation** | openapi-typescript | Auto-generate TS interfaces from FastAPI's OpenAPI schema — keeps backend/frontend types in sync |

### Why These Choices

- **FastAPI over Flask** — API-first architecture needs an API-first framework. Auto-generated OpenAPI docs, Pydantic validation, native async, WebSocket built in.
- **Vue 3 over React** — lighter, less boilerplate. Composition API maps cleanly to our plugin pattern. Pinia is simpler than Redux. Single-file components keep modules self-contained.
- **Vue 3 over server-rendered HTML** — this will grow into a life OS. Interactive dashboards, real-time feeds, charts, search — that's app territory, not template territory.
- **Session cookies over JWT** — JWT in an SPA means choosing between localStorage (XSS-vulnerable) and httpOnly cookies (needs CSRF protection anyway). Signed httpOnly session cookies via FastAPI + itsdangerous are simpler: no token refresh, no client-side storage, secure by default. Logout actually works. OAuth is a future upgrade path if needed.
- **PrimeVue over building from scratch** — DataTable (sort, filter, paginate), Modal, Sidebar, tabs, etc. already exist and are well-tested. Customise the dark theme to match the aesthetic. Building nine non-trivial components from scratch is weeks of work for marginal benefit.
- **No Redis/message queue** — overkill at current scale. WebSocket for real-time, direct DB queries for data.
- **CORS** — development: FastAPI CORS middleware (Vue dev server runs on a different port). Production: serve Vue build via FastAPI `StaticFiles` mount — single origin, no CORS needed.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       MISSION CONTROL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐     │
│   │               FastAPI Backend                         │     │
│   │                                                       │     │
│   │  Core: Auth, Module Registry, Config, WebSocket hub   │     │
│   │                                                       │     │
│   │  ┌────────────┐ ┌────────────┐ ┌────────────┐        │     │
│   │  │ Router:    │ │ Router:    │ │ Router:    │  ...   │     │
│   │  │ /api/memory│ │ /api/school│ │ /api/agents│        │     │
│   │  │ (📜)       │ │ (🏥)       │ │ (🤖)       │        │     │
│   │  └────────────┘ └────────────┘ └────────────┘        │     │
│   │                                                       │     │
│   │  Pydantic models │ Async DB │ File watchers           │     │
│   └──────────┬────────────────────────────────────────────┘     │
│              │                                                   │
│         JSON API + WebSocket                                     │
│              │                                                   │
│   ┌──────────▼────────────────────────────────────────────┐     │
│   │               Vue 3 + Vite Frontend                   │     │
│   │                                                       │     │
│   │  ┌────────────┐ ┌────────────┐ ┌────────────┐        │     │
│   │  │ Module:    │ │ Module:    │ │ Module:    │  ...   │     │
│   │  │ Memory     │ │ School     │ │ Agents     │        │     │
│   │  │ views/     │ │ views/     │ │ views/     │        │     │
│   │  │ components/│ │ components/│ │ components/│        │     │
│   │  │ store.ts   │ │ store.ts   │ │ store.ts   │        │     │
│   │  └────────────┘ └────────────┘ └────────────┘        │     │
│   │                                                       │     │
│   │  Shared: layout, nav, cards, charts, tables, theme    │     │
│   │  Router: vue-router (auto-registered from modules)    │     │
│   │  State: Pinia (per-module stores)                     │     │
│   └───────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Extensibility

This is the whole point. Adding a new life domain should be trivial.

**Adding a module requires:**
1. Drop in a module folder (backend router + frontend views)
2. It auto-registers — appears in sidebar, gets its own page, contributes widgets to Overview

**Adding a module does NOT require:**
- Editing core routing or app config
- Creating templates from scratch
- Touching other modules' code

**Module isolation:** Each module's router is wrapped in error-handling middleware. If the School module throws an unhandled exception, the rest of the app keeps running — that module's endpoints return 503 and its Overview widget shows "unavailable." Modules should also degrade gracefully when their data sources are down (Postgres offline, OpenClaw unreachable, memory files unmounted).

### Backend — one file to register:

```python
# backend/modules/finance/__init__.py
from .router import router

MODULE_INFO = {
    "id": "finance",
    "name": "Finance",
    "icon": "💰",
    "router": router,
    "prefix": "/api/finance",
}
```

### Frontend — one routes file + components:

```typescript
// frontend/src/modules/finance/routes.ts
export default {
  module: {
    id: 'finance',
    name: 'Finance',
    icon: '💰',
    navOrder: 5,
  },
  routes: [
    { path: '/finance', component: () => import('./FinancePage.vue') },
  ],
  overviewWidgets: [
    () => import('./widgets/SpendingSummary.vue'),
  ],
}
```

---

## Project Structure

```
mission-control/
│
├── backend/                          # FastAPI (Python)
│   ├── main.py                       # App factory, module auto-discovery
│   ├── core/
│   │   ├── config.py                 # Settings, DB connection, env
│   │   ├── auth.py                   # Auth middleware
│   │   ├── registry.py               # Module registry — auto-discovers routers
│   │   ├── database.py               # Async Postgres (asyncpg)
│   │   ├── websocket.py              # WebSocket hub for real-time feeds
│   │   └── models.py                 # Shared Pydantic base models
│   ├── modules/
│   │   ├── memory/                   # 📜 Memory API
│   │   │   ├── __init__.py           # MODULE_INFO
│   │   │   ├── router.py             # /api/memory/*
│   │   │   ├── models.py             # Pydantic schemas
│   │   │   └── service.py            # Business logic
│   │   ├── school/                   # 🏥 School API
│   │   │   └── ...
│   │   ├── agents/                   # 🤖 Agent Activity API
│   │   │   └── ...
│   │   └── ...                       # Future modules
│   ├── Dockerfile
│   ├── pyproject.toml                # Python deps (uv)
│   └── tests/                        # pytest tests
│
├── frontend/                         # Vue 3 + Vite (TypeScript)
│   ├── src/
│   │   ├── App.vue                   # Root layout
│   │   ├── main.ts                   # Bootstrap + plugin registration
│   │   ├── router/index.ts           # Auto-imports module routes
│   │   ├── stores/app.ts             # Global state (auth, nav, theme)
│   │   ├── components/               # Shared UI components
│   │   │   ├── layout/               # Sidebar, Header, PageShell
│   │   │   ├── data/                 # StatCard, DataTable, Timeline, Chart
│   │   │   └── ui/                   # Badge, SearchBar, Modal
│   │   ├── modules/
│   │   │   ├── overview/             # 🏠 Home — assembles widgets
│   │   │   ├── memory/               # 📜 Explorer, search, viewer
│   │   │   ├── school/               # 🏥 Events, emails, tasks
│   │   │   ├── agents/               # 🤖 Status, runs, cron
│   │   │   └── ...                   # Future modules
│   │   ├── composables/              # useApi, useWebSocket, useModule
│   │   └── styles/                   # theme.css, base.css
│   ├── vite.config.ts
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## Data Model

### New Postgres Tables

```sql
-- Agent run history (unified across all agents)
CREATE TABLE IF NOT EXISTS agent_runs (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    run_type VARCHAR(50),              -- 'cron', 'spawn', 'query', 'manual'
    trigger VARCHAR(100),              -- cron job name, spawn source, or 'dashboard'
    status VARCHAR(20),
    summary TEXT,
    duration_ms INT,
    tokens_used INT,
    metadata JSONB DEFAULT '{}',       -- agent-specific data (memories_added, emails_processed, etc.)
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_runs_agent_id ON agent_runs(agent_id);
CREATE INDEX idx_agent_runs_created_at ON agent_runs(created_at DESC);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
```

> **Implemented:** The actual table uses UUID primary keys (not SERIAL), timezone-aware timestamps, and VARCHAR(100) for agent_id. See `backend/core/models.py` for the SQLAlchemy model.

> **Note: No `memory_entries` table.** The original plan had a Postgres index of memory file metadata. This creates a sync problem — when agents modify markdown files, who updates the table? Instead: read memory files directly via the API and cache in-memory with a file watcher invalidation. If search performance becomes a problem, add full-text indexing later with a rebuild-from-source script, not a dual-write.

### Data Sources

| Data | Source | Method |
|------|--------|--------|
| Memory files | `~/.openclaw/workspace/memory/*.md` | File read (Docker volume mount) |
| MEMORY.md | `~/.openclaw/workspace/MEMORY.md` | File read |
| School data | Postgres (`school_emails`, `school_events`, etc.) | Async DB query |
| Agent runs | Postgres (`agent_runs`) | Async DB query |
| Cron status | OpenClaw gateway API (`:18789`) | HTTP |

---

## Pages

### 🏠 Overview
Landing page. Stats bar + widget grid assembled from all registered modules. Live activity timeline via WebSocket.

### 📜 Memory Explorer
Search and browse memories. Full-text search, timeline view, category filters, MEMORY.md viewer with section navigation. The killer feature — "what did we decide about X?" with source citations.

### 🏥 School
Port of Matron's dashboard. Events (today/week/upcoming), emails, action items, stats. Same Postgres data, same functionality, better home.

### 🤖 Agents
Agent status cards, run history table with filters, cron schedule, trigger buttons. Unified view across all agents.

### 📊 Analytics (stretch)
Memory growth, agent activity trends, email processing stats. Sparkline charts on Overview.

---

## Wireframe

```
┌──┬───────────────────────────────────────────────────────────┐
│  │  🧠 Mission Control                    Thu 13 Feb 2026    │
│  ├───────────────────────────────────────────────────────────┤
│S │                                                           │
│I │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│D │  │  42     │ │   3     │ │  12     │ │   9     │        │
│E │  │Memories │ │ Agents  │ │ Runs    │ │ Emails  │        │
│B │  │         │ │ Active  │ │ Today   │ │Processed│        │
│A │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│R │                                                           │
│  │  ┌───────────────────────┐  ┌───────────────────────┐    │
│🏠│  │ 🤖 Agent Status       │  │ ⚡ Live Activity       │    │
│📜│  │                       │  │                       │    │
│🏥│  │ 🫖 Jeeves      ✅ now │  │ 10:09 Nick asked      │    │
│🤖│  │ 🏥 Matron    ✅ 09:30 │  │       memory status   │    │
│📊│  │ 📜 Archivist ✅ 09:00 │  │ 09:02 📜 Chat log     │    │
│  │  │                       │  │       (nothing new)   │    │
│  │  │ [Trigger Run ▶]       │  │ 07:00 🏥 Daily digest  │    │
│  │  └───────────────────────┘  │       → Telegram ✅   │    │
│  │                              │ 02:00 📜 Consolidation│    │
│  │  ┌───────────────────────┐  │       4 promoted      │    │
│  │  │ 🧠 Recent Memories    │  └───────────────────────┘    │
│  │  │                       │                               │
│  │  │ • Memory layer built  │  ┌───────────────────────┐    │
│  │  │   (2026-02-12)        │  │ 🏥 School Today       │    │
│  │  │ • Gemini embeddings   │  │                       │    │
│  │  │   configured          │  │ Nothing scheduled 🎉  │    │
│  │  │                       │  │ Fri — Natty, homework  │    │
│  │  │ [View All →]          │  │ [View All →]          │    │
│  │  └───────────────────────┘  └───────────────────────┘    │
│  │                                                           │
└──┴───────────────────────────────────────────────────────────┘
```

**UI patterns:** Collapsible sidebar, widget grid, WebSocket live feed, trigger buttons, dark theme, mobile responsive (sidebar → bottom nav).

---

## API Design

```
GET  /api/health                     → app health + module status + DB connectivity
GET  /api/modules                    → registered modules + metadata
GET  /api/memory/search?q=...        → full-text search across memory files (in-process, not embedding-based)
GET  /api/memory/files               → list memory files with metadata
GET  /api/memory/files/{date}        → daily memory content (rendered markdown)
GET  /api/memory/long-term           → MEMORY.md with section navigation
GET  /api/school/events              → events (filters: child, date range)
GET  /api/school/emails              → processed emails
GET  /api/school/stats               → Matron statistics
GET  /api/agents                     → agent list + status
GET  /api/agents/{id}/runs           → run history (paginated, filterable)
GET  /api/agents/cron                → cron schedule + status (via OpenClaw gateway HTTP call)
POST /api/agents/{id}/trigger        → trigger agent run (HTTP call to OpenClaw gateway API)
WS   /ws/live                        → real-time activity stream
```

Auto-generated docs at `/docs` (Swagger) and `/redoc`.

### WebSocket Protocol

The `/ws/live` endpoint uses a simple JSON message format with topic-based filtering:

```json
{ "topic": "agent_run", "agent": "matron", "status": "ok", "summary": "Daily digest sent", "ts": "..." }
{ "topic": "memory",    "action": "consolidation", "memories_added": 4, "ts": "..." }
```

Clients send a subscribe message on connect: `{ "subscribe": ["agent_run", "memory", "school"] }`. Default: all topics. Modules publish events via a shared `EventBus` in the backend — the WebSocket hub broadcasts to subscribed clients. Reconnection with exponential backoff handled by `useWebSocket` composable on the frontend.

### Trigger Mechanism

`POST /api/agents/{id}/trigger` sends an HTTP request to the OpenClaw gateway API at `:18789`, which manages agent execution. Mission Control does not spawn processes directly — it's a control plane consumer, not the execution engine. The endpoint returns immediately with a run ID; status updates arrive via WebSocket. If the gateway is unreachable, the trigger returns 503 with a clear error.

---

## Implementation Plan

| Phase | Work | Estimate |
|-------|------|----------|
| **1. Scaffolding** | FastAPI factory + module registry + Alembic, Vue 3 + Vite + PrimeVue + Pinia, docker-compose.dev.yml, openapi-typescript pipeline | ~5 hrs |
| **2. Shell + theme** | App layout (Sidebar, Header, PageShell), PrimeVue dark theme customisation, shared composables (useApi, useWebSocket), StatCard component | ~3 hrs |
| **3. Module: Memory** | File reader, full-text search, markdown renderer. MemoryPage, search, MEMORY.md viewer, RecentMemories widget. *The killer feature — build it first.* | ~5 hrs |
| **4. Module: Agents** | Agent status + cron (OpenClaw HTTP) + run history APIs. AgentsPage, RunHistory, AgentStatus widget. WebSocket live feed. Trigger mechanism. | ~5 hrs |
| **5. Module: School** | Port Matron queries to FastAPI router. SchoolPage, events, emails, tasks, TodayEvents widget. Side-by-side parity check with Matron. | ~4 hrs |
| **6. Overview** | Widget assembly from all modules. Activity timeline. Stats bar. Health check endpoint. | ~3 hrs |
| **7. Docker + deploy** | Multi-stage Dockerfile (Vite build → FastAPI static mount). Replace matron-dashboard container. Alembic migration on startup. | ~2 hrs |
| **8. Polish + testing** | Mobile responsive, error handling, loading states, WebSocket reconnect, module contract tests, API integration tests. | ~4 hrs |
| **Total** | | **~31 hrs** |

New modules after this: **~4-6 hours each.**

---

## Development Workflow

Local development runs both servers with hot reload — no Docker rebuild cycle during development.

- **Backend:** `uvicorn main:app --reload` — auto-restarts on Python file changes
- **Frontend:** `vite dev` with proxy config pointing API requests to the backend port — hot module replacement, sub-second feedback
- **Migrations:** Alembic for all schema changes. `alembic revision --autogenerate -m "description"` to generate, `alembic upgrade head` to apply. Migrations are version-controlled alongside code.
- **Docker:** `docker-compose.dev.yml` with volume mounts for live code. Production uses a multi-stage build (Vite build → serve static via FastAPI `StaticFiles` mount).
- **Type sync:** Run `openapi-typescript` against FastAPI's `/openapi.json` after API changes to regenerate frontend types. Can be a pre-commit hook or dev script.

---

## Testing

- **Backend:** pytest + httpx (`TestClient`). Each module gets a `tests/` directory with API integration tests against a test database. Core registry gets a smoke test verifying all modules load without error.
- **Frontend:** Vitest for component and composable unit tests. Playwright for E2E smoke tests (stretch — add once the app is stable).
- **Module contract:** A test that auto-discovers all modules and validates their `MODULE_INFO` structure and route registration. If a new module breaks the contract, CI catches it immediately.

---

## Matron Transition

Mission Control replaces Matron's dashboard, but the transition should be safe.

- **During development:** Run Mission Control on a different port alongside Matron. Both read from the same Postgres tables — no data conflicts.
- **Feature parity gate:** School module is ready for cutover when it matches Matron's existing views (events, emails, action items, stats). Side-by-side comparison before switching.
- **Cutover:** Swap Docker containers. If using the same port (`:5050`), it's a single container replacement. If new port, update bookmarks/Tailscale.
- **Rollback:** Keep the `matron-dashboard` Docker image tagged. If Mission Control has issues, re-deploy Matron in minutes.
- **Decommission:** Remove Matron's Flask code and `agent_log` table once the School module has been stable for a reasonable period. Migrate any `agent_log` history into `agent_runs` via a one-time script.

---

## Decisions (confirmed 2026-02-13)

1. **Port** — `:5055` during development, take over `:5050` at Matron cutover
2. **External access** — Yes, via Tailscale. Session cookies with `Secure` flag + Tailscale domain.
3. **Alerts** — Yes. Flag anomalies (agent overdue, failed runs). Simple cron checking `agent_runs` + expected schedules.
4. **Memory editing** — Read-only in v1. Nick edits via filesystem.
5. **First non-agent module** — TBC, parked

---

## Related

- [[Archivist - Architecture]] — memory curator, powers the Memory module
- [[Matron - Architecture]] — school comms, powers the School module
- [[Mission Control - Modules]] — full module registry
