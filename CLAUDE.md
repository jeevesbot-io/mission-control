# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mission Control is a unified dashboard and life operating system. It replaces Matron's standalone Flask dashboard with a plugin-based platform where each life domain (agents, memory, school, health, finance, etc.) is a self-contained module. **Status: All build phases (1–8) complete. Core system, all modules (Memory, Agents, School, Overview), WebSocket live feed, Docker production build, and full test suite are live. Ready for deployment and Matron cutover.**

All architecture documentation lives in `docs/`:
- `Mission Control - Architecture.md` — full technical blueprint (stack, structure, API, wireframes, implementation plan)
- `Mission Control - Modules.md` — module registry and contracts
- `Mission Control - Backlog.md` — build phases and future features
- `Mission Control - Architecture.md` also covers the implementation plan and phase estimates

## Tech Stack

- **Backend:** FastAPI (Python), async, Pydantic validation, Alembic migrations
- **Frontend:** Vue 3 + Vite (TypeScript), Pinia state management, PrimeVue components, Apache ECharts
- **Database:** Postgres (`jeeves` DB) — shared with existing Matron tables
- **Real-time:** WebSocket at `/ws/live` for agent activity feeds
- **Auth:** Signed httpOnly session cookies (itsdangerous), no JWT
- **Type sync:** `openapi-typescript` generates frontend types from FastAPI's `/openapi.json`
- **Deployment:** Docker via Colima, multi-stage build (Vite build → FastAPI StaticFiles mount)

## Development Commands

```bash
# Backend (from backend/)
uv run uvicorn main:app --reload --port 5055

# Frontend (from frontend/)
npm run dev                 # proxied to backend at :5055

# Migrations (from backend/)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Type generation (from frontend/, backend must be running)
npm run generate-types

# Testing
cd backend && uv run pytest       # backend (42 tests)
cd frontend && npm test            # frontend vitest (41 tests)
cd frontend && npx playwright test # e2e tests (requires backend + frontend running)

# Docker (development)
docker-compose -f docker-compose.dev.yml up

# Docker (production — single container, serves frontend via FastAPI)
docker-compose up
```

## Architecture

Plugin-based monolith with auto-discovery. The core system provides auth, routing, WebSocket hub, and module registry. Each module is fully self-contained — adding one requires no changes to core code.

### Module Contract

Every module provides two registration points that are auto-discovered:

**Backend** (`backend/modules/<name>/__init__.py`):
```python
MODULE_INFO = {
    "id": "module_name",
    "name": "Display Name",
    "icon": "🔮",
    "router": router,          # FastAPI APIRouter
    "prefix": "/api/module",
}
```

**Frontend** (`frontend/src/modules/<name>/routes.ts`):
```typescript
export default {
  module: { id, name, icon, navOrder },
  routes: [...],               // vue-router routes
  overviewWidgets: [...],      // components for Overview page
}
```

### Module Isolation

Each module's router is wrapped in error-handling middleware. If one module throws, others keep running — the failing module returns 503 and its Overview widget shows "unavailable." Modules must degrade gracefully when their data sources are down.

### Project Structure

```
mission-control/
├── backend/
│   ├── main.py              # App factory, module auto-discovery
│   ├── pyproject.toml       # Python deps (managed by uv)
│   ├── alembic.ini          # Migration config
│   ├── alembic/             # Migration scripts
│   ├── core/                # Auth, registry, config, DB, WebSocket hub
│   ├── modules/             # overview/, memory/, agents/, school/
│   │   └── <name>/
│   │       ├── __init__.py  # MODULE_INFO
│   │       ├── router.py    # API endpoints
│   │       ├── models.py    # Pydantic schemas
│   │       └── service.py   # Business logic
│   └── tests/               # pytest tests (42 tests)
├── frontend/
│   ├── src/
│   │   ├── router/          # Auto-imports module routes
│   │   ├── stores/          # Pinia stores (app, per-module)
│   │   ├── components/      # Shared: layout/, data/, ui/
│   │   ├── modules/         # overview/, memory/, school/, agents/
│   │   ├── composables/     # useApi, useWebSocket, useModule
│   │   └── styles/          # base.css
│   ├── vite.config.ts
│   └── package.json
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Production (port 5050)
├── docker-compose.dev.yml   # Development (separate services)
└── scripts/
    └── generate-types.sh
```

## Data Sources

| Data | Source | Access Method |
|------|--------|---------------|
| Memory files | `~/.openclaw/workspace/memory/*.md` | File read (Docker volume mount), cached in-memory with file watcher |
| MEMORY.md | `~/.openclaw/workspace/MEMORY.md` | File read |
| School data | Postgres (`school_emails`, `school_events`, `todoist_tasks`) | Async DB query |
| Agent runs | Postgres (`agent_runs`) | Async DB query |
| Cron status | OpenClaw gateway API (`:18789`) | HTTP |

No `memory_entries` table — memory files are the source of truth. No Redis or message queue.

## Key Design Decisions

- **Port:** `:5055` during development, takes over `:5050` at Matron cutover
- **Memory editing:** Read-only in v1; edited via filesystem directly
- **Search:** Full-text on markdown files first; semantic/embedding search only if needed later
- **CORS:** Dev uses FastAPI middleware; production serves static via single-origin FastAPI mount
- **Agent triggers:** `POST /api/agents/{id}/trigger` sends HTTP to OpenClaw gateway — Mission Control is the control plane, not the execution engine
- **WebSocket protocol:** Topic-based JSON messages; clients subscribe on connect; `useWebSocket` composable handles reconnection with exponential backoff

## Build Phases (all complete)

1. ~~Scaffolding~~ — FastAPI + Alembic + Vue 3 + Vite + PrimeVue + openapi-typescript
2. ~~Shell + theme~~ — layout, dark/light theme, shared composables, Ground Control design system
3. ~~Memory module~~ — file browser, full-text search, MEMORY.md viewer, TOC navigation
4. ~~Agents module + WebSocket~~ — agent list, run history, cron, triggers, live activity feed
5. ~~School module~~ — events, emails, tasks (tabbed view), stats from existing Postgres tables
6. ~~Overview page~~ — unified dashboard with `/api/overview` aggregating all system data, health checks, upcoming events, agent activity feed, stat cards
7. ~~Docker + deploy~~ — multi-stage production Dockerfile, production docker-compose on port 5050
8. ~~Polish + testing~~ — 42 backend tests, 41 frontend tests, Playwright e2e test suites

## API Endpoints

```
GET  /api/health                     → health + version
GET  /api/modules                    → registered modules
GET  /api/overview                   → aggregated dashboard data (health, stats, events, activity)
GET  /api/memory/files               → daily memory file list
GET  /api/memory/files/{date}        → daily memory content + sections
GET  /api/memory/long-term           → MEMORY.md content + sections
GET  /api/memory/search?q=...        → full-text search
GET  /api/memory/stats               → memory stats
GET  /api/agents/                    → agent list with last run info
GET  /api/agents/stats               → aggregate stats (runs, success rate, 24h)
GET  /api/agents/{id}/runs           → paginated run history (filterable)
GET  /api/agents/cron                → cron schedule from OpenClaw gateway
POST /api/agents/{id}/trigger        → trigger agent via gateway + WebSocket broadcast
GET  /api/school/events              → upcoming school events
GET  /api/school/emails              → recent school emails
GET  /api/school/tasks               → todoist tasks
GET  /api/school/stats               → school summary stats
WS   /ws/live                        → real-time activity (topic-based pub/sub)
```
