# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mission Control is a unified dashboard and life operating system — a plugin-based platform where each life domain (agents, memory, school, health, finance, etc.) is a self-contained module. All build phases (1–9) are complete. Active modules: Memory, Agents, School, Overview, War Room, Calendar, Chat, Content Pipeline, Office View, Activity Timeline.

## Tech Stack

- **Backend:** FastAPI (Python 3.13+), async, Pydantic v2, Alembic migrations, `uv` package manager
- **Frontend:** Vue 3 + Vite (TypeScript), Pinia, PrimeVue, Apache ECharts
- **Database:** Postgres (`jeeves` DB) — shared with existing Matron tables, raw SQL via SQLAlchemy async
- **Real-time:** WebSocket at `/ws/live` (topic-based pub/sub)
- **Auth:** Signed httpOnly session cookies (itsdangerous), no JWT
- **Type sync:** `openapi-typescript` generates `frontend/src/types/api.ts` from FastAPI's `/openapi.json`
- **Deployment:** Docker via Colima, multi-stage build (Vite → FastAPI StaticFiles)

## Development Commands

```bash
# Initial setup
cd backend && uv sync
cd frontend && npm install

# Backend (from backend/)
uv run uvicorn main:app --reload --port 5055

# Frontend (from frontend/) — dev server at :5173, proxied to :5055
npm run dev

# Linting (from backend/)
uv run ruff check .

# Migrations (from backend/)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Type generation (from frontend/, backend must be running)
npm run generate-types

# Testing
cd backend && uv run pytest                        # 86 tests
cd backend && uv run pytest tests/test_memory.py  # single file
cd frontend && npm test                            # 77 vitest tests
cd frontend && npm test -- src/modules/warroom/store.test.ts  # single file
cd frontend && npx playwright test                 # e2e (requires both servers running)

# Docker
docker-compose -f docker-compose.dev.yml up       # development
docker-compose up                                  # production (port 5050)
```

API docs available at `http://localhost:5055/docs` (Swagger) and `/redoc`.

## Architecture

Plugin-based monolith with auto-discovery. The core system provides auth, routing, WebSocket hub, and module registry. Each module is fully self-contained — adding one requires no changes to core code.

### Module Contract

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

Both are auto-discovered at startup — no registration needed in core code.

### Module Isolation

Each module router is wrapped in error-handling middleware. A failing module returns 503 and its Overview widget shows "unavailable." Other modules keep running.

### Project Structure

```
mission-control/
├── backend/
│   ├── main.py              # App factory, module auto-discovery
│   ├── core/                # auth, config, database, websocket hub, registry, rate_limit
│   ├── modules/             # activity/, agents/, calendar/, chat/, content/, memory/, office/, overview/, school/, warroom/
│   │   └── <name>/
│   │       ├── __init__.py  # MODULE_INFO
│   │       ├── router.py    # API endpoints
│   │       ├── models.py    # Pydantic schemas
│   │       └── service.py   # Business logic
│   └── tests/               # 79 pytest tests (one file per module)
├── frontend/src/
│   ├── router/              # Auto-imports module routes
│   ├── stores/              # Pinia stores (app-level + per-module)
│   ├── components/          # Shared: layout/, data/, ui/
│   ├── modules/             # activity/, agents/, calendar/, chat/, content/, memory/, office/, overview/, school/, warroom/
│   ├── composables/         # useApi, useWebSocket, useModule
│   └── types/api.ts         # Generated from FastAPI OpenAPI spec
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Production (port 5050)
├── docker-compose.dev.yml   # Development
└── docs/                    # Architecture docs, module registry, backlog
```

## Data Sources

| Data | Source | Access Method |
|------|--------|---------------|
| Memory files | `~/.openclaw/workspace/memory/*.md` | File read + in-memory cache with file watcher |
| MEMORY.md | `~/.openclaw/workspace/MEMORY.md` | File read |
| Family calendar | Google Calendar (`sollyfamily3@gmail.com`) | `gog` CLI subprocess |
| School data | Postgres (`school_emails`, `school_events`, `todoist_tasks`) | Async raw SQL |
| Agent activity | Postgres (`agent_log`) | Async raw SQL |
| Cron jobs | OpenClaw gateway API (`:18789`) | HTTP |
| Tasks / Projects | `~/.openclaw/workspace/dashboard/data/tasks.json`, `projects.json` | File read/write (thread-locked) |
| Skills | `~/.openclaw/skills/`, `~/.openclaw/workspace/skills/` | Filesystem scan |
| Soul files | `~/.openclaw/workspace/SOUL.md`, `IDENTITY.md`, `USER.md`, `AGENTS.md` | File read/write with 20-entry history |
| OpenClaw config | `~/.openclaw/openclaw.json` | File read/write (model, skill enabled state) |
| Usage sessions | `~/.openclaw/agents/main/sessions/*.jsonl` | Parsed async, 60s TTL cache |
| Content pipeline | `~/.openclaw/workspace/dashboard/data/content.json` | File read/write |
| Activity events | `~/.openclaw/workspace/dashboard/data/activity.json` | File read/write (capped 1000 entries) |

No `memory_entries` table — memory files are the source of truth. No Redis or message queue.

## Key Design Decisions

- **Port:** `:5055` dev, `:5050` production (Matron cutover)
- **Agent triggers:** `POST /api/agents/{id}/trigger` sends HTTP to OpenClaw gateway — Mission Control is the control plane, not the execution engine
- **WebSocket protocol:** Topic-based JSON messages; `useWebSocket` composable handles reconnection with exponential backoff
- **Memory editing:** Read-only in v1; edited via filesystem directly
- **CORS:** Dev uses FastAPI middleware; production serves static via single-origin FastAPI mount
- **Rate limiting:** `slowapi` on sensitive endpoints (e.g. chat: 30/minute)

## API Endpoints

```
GET  /api/health
GET  /api/modules
GET  /api/overview

# Memory
GET  /api/memory/files
GET  /api/memory/files/{date}
GET  /api/memory/long-term
GET  /api/memory/search?q=...
GET  /api/memory/stats

# Agents
GET  /api/agents/
GET  /api/agents/stats
GET  /api/agents/{id}/log
GET  /api/agents/cron
POST /api/agents/{id}/trigger

# School
GET  /api/school/calendar
GET  /api/school/events
GET  /api/school/emails
GET  /api/school/tasks
GET  /api/school/stats

# Calendar
GET  /api/calendar/?start_date=&days_ahead=14
GET  /api/calendar/jobs

# Chat
POST /api/chat/send
GET  /api/chat/health

# Content Pipeline
GET    /api/content/
POST   /api/content/
PATCH  /api/content/{item_id}
DELETE /api/content/{item_id}
POST   /api/content/{item_id}/move/{target_stage}

# Office View
GET  /api/office/

# War Room
GET    /api/warroom/tasks
POST   /api/warroom/tasks
PUT    /api/warroom/tasks/{id}
DELETE /api/warroom/tasks/{id}
GET    /api/warroom/tasks/queue
POST   /api/warroom/tasks/{id}/pickup
POST   /api/warroom/tasks/{id}/complete
GET    /api/warroom/projects
POST   /api/warroom/projects
PUT    /api/warroom/projects/{id}
DELETE /api/warroom/projects/{id}
GET    /api/warroom/tags
GET    /api/warroom/usage
GET    /api/warroom/models
POST   /api/warroom/model
GET    /api/warroom/heartbeat
POST   /api/warroom/heartbeat
GET    /api/warroom/skills
POST   /api/warroom/skills
POST   /api/warroom/skills/{id}/toggle
DELETE /api/warroom/skills/{id}
GET    /api/warroom/workspace-file
PUT    /api/warroom/workspace-file
GET    /api/warroom/workspace-file/history
GET    /api/warroom/soul/templates
GET    /api/warroom/calendar
GET    /api/warroom/stats

# Activity Timeline
GET  /api/activity/feed?limit=50&cursor=&module=&actor=&action=
GET  /api/activity/stats

WS   /ws/live
```
