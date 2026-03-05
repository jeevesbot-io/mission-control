# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mission Control** is an agent orchestration dashboard -- a plugin-based platform for managing autonomous agents, tasks, and workflows. It replaces a previous Flask dashboard (Matron) with a proper full-stack platform.

All build phases (1-9) are complete. Refactoring in progress (Phase 1 done). Active modules: Memory, Agents, Overview, War Room, Calendar, Chat, Content Pipeline, Office View, Activity Timeline. School module extracted to `~/projects/FamilyDashboard/` (Phase 1, 2026-03-05).

## Tech Stack

- **Backend:** FastAPI (Python 3.13+), async throughout, Pydantic v2, SQLAlchemy async (raw SQL), Alembic migrations
- **Frontend:** Vue 3 + Vite (TypeScript), Pinia state management, PrimeVue components, Apache ECharts charts, Lucide icons
- **Database:** Postgres (`jeeves` DB) -- shared with existing Matron tables, accessed via asyncpg
- **Real-time:** WebSocket at `/ws/live` (topic-based pub/sub via `ConnectionManager`)
- **Auth:** Signed httpOnly session cookies (itsdangerous), Cloudflare Access in production -- no JWT
- **Type sync:** `openapi-typescript` generates `frontend/src/types/api.ts` from FastAPI's `/openapi.json`
- **Package management:** `uv` (backend), `npm` (frontend)
- **Linting:** ruff (backend), vue-tsc (frontend type checking)
- **Testing:** pytest + pytest-asyncio (backend, 110 tests), vitest (frontend, 69 tests), Playwright (e2e)
- **Deployment:** Docker via Colima, multi-stage build (Vite -> FastAPI StaticFiles), port 5050 production

## Development Commands

```bash
# Initial setup
cd backend && uv sync
cd frontend && npm install

# Backend (from backend/)
uv run uvicorn main:app --reload --port 5055

# Frontend dev server (from frontend/) -- serves at :5173, proxied to :5055
npm run dev

# Run backend tests (from backend/)
uv run pytest                        # all 107 tests
uv run pytest tests/test_memory.py   # single module
uv run pytest -k "test_warroom"      # by keyword

# Run frontend tests (from frontend/)
npm test                             # all 77 vitest tests
npm test -- src/modules/warroom/store.test.ts  # single file

# Run e2e tests (from frontend/, requires both servers running)
npx playwright test

# Lint backend (from backend/)
uv run ruff check .

# Generate TypeScript types (from frontend/, backend must be running on :5055)
npm run generate-types

# Database migrations (from backend/)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Docker
docker-compose -f docker-compose.dev.yml up   # development
docker-compose up                              # production (port 5050)

# Build frontend for production (from frontend/)
npm run build    # outputs to frontend/dist/
```

API docs: `http://localhost:5055/docs` (Swagger) and `/redoc`

## Architecture

Plugin-based monolith with auto-discovery. The core system provides auth, routing, WebSocket hub, rate limiting, and module registry. Each module is fully self-contained -- adding one requires zero changes to core code.

### Module Auto-Discovery

**Backend** (`backend/core/registry.py`): Scans `backend/modules/` at startup. Each module package exports `MODULE_INFO` dict with keys: `id`, `name`, `icon`, `router` (FastAPI APIRouter), `prefix`.

**Frontend** (`frontend/src/router/`): Auto-imports `routes.ts` from each module in `frontend/src/modules/`. Each exports: `module` (id, name, icon, navOrder), `routes` (vue-router routes), `overviewWidgets` (optional).

### Module Contract

Backend module (`backend/modules/<name>/__init__.py`):
```python
MODULE_INFO = {
    "id": "module_name",
    "name": "Display Name",
    "icon": "...",
    "router": router,          # FastAPI APIRouter
    "prefix": "/api/module",
}
```

Frontend module (`frontend/src/modules/<name>/routes.ts`):
```typescript
export default {
  module: { id, name, icon, navOrder },
  routes: [...],               // vue-router routes
  overviewWidgets: [...],      // components for Overview page
}
```

### Module Isolation

Each module router is wrapped in error-handling middleware. A failing module returns 503; its Overview widget shows "unavailable." Other modules keep running.

### WebSocket Protocol

Topic-based pub/sub at `/ws/live`. Clients send JSON: `{"action": "subscribe", "topic": "warroom"}`. Server broadcasts `{"topic": "warroom", "data": {...}}` to subscribers. The `useWebSocket` composable handles reconnection with exponential backoff.

## Project Structure

```
MissionControls/
+-- backend/
|   +-- main.py              # App factory, module auto-discovery, WebSocket endpoint, SPA serving
|   +-- core/
|   |   +-- auth.py          # Session cookie auth
|   |   +-- cloudflare_auth.py  # Cloudflare Access middleware (production)
|   |   +-- config.py        # Pydantic Settings (all env vars)
|   |   +-- constants.py     # Shared constants
|   |   +-- database.py      # SQLAlchemy async engine + session factory
|   |   +-- logging_config.py
|   |   +-- models.py        # Shared Pydantic response models
|   |   +-- rate_limit.py    # slowapi rate limiter
|   |   +-- registry.py      # Module auto-discovery logic
|   |   +-- security_headers.py  # Security headers middleware
|   |   +-- websocket.py     # ConnectionManager (topic pub/sub)
|   +-- modules/
|   |   +-- activity/        # Activity Timeline feed
|   |   +-- agents/          # Agent management + triggers
|   |   +-- calendar/        # Google Calendar via gog CLI
|   |   +-- chat/            # Chat interface (rate-limited 30/min)
|   |   +-- content/         # Content Pipeline (Kanban stages)
|   |   +-- memory/          # Memory file viewer + search
|   |   +-- office/          # Office View (agent status overview)
|   |   +-- overview/        # Dashboard Overview (widget aggregation)
|   |   +-- warroom/         # War Room (task management, projects, skills, soul files)
|   +-- alembic/             # Database migration scripts
|   +-- tests/               # 110 pytest tests (one file per module + test_health.py)
|   +-- pyproject.toml       # Python deps and tool config
+-- frontend/
|   +-- src/
|   |   +-- router/          # Auto-imports module routes
|   |   +-- stores/          # Pinia stores (app-level + per-module)
|   |   +-- components/      # Shared: layout/, data/, ui/
|   |   +-- modules/         # Mirror of backend modules (Vue components + stores)
|   |   +-- composables/     # useApi, useWebSocket, useModule
|   |   +-- types/api.ts     # Auto-generated from FastAPI OpenAPI spec
|   +-- e2e/                 # Playwright e2e tests
|   +-- package.json
|   +-- vite.config.ts       # Dev proxy: /api -> :5055, /ws -> ws://:5055
|   +-- tsconfig.*.json
+-- scripts/
|   +-- generate-types.sh    # Type generation helper
+-- Dockerfile               # Multi-stage production build
+-- docker-compose.yml       # Production (port 5050)
+-- docker-compose.dev.yml   # Development
+-- .env.example             # Environment variable template
+-- docs/                    # Symlink -> Obsidian vault
```

## Active Modules

| Module | Backend Prefix | Purpose |
|--------|---------------|---------|
| Overview | `/api/overview` | Dashboard home, aggregates widgets from all modules |
| Memory | `/api/memory` | Browse/search memory markdown files |
| Agents | `/api/agents` | Agent list, logs, stats, trigger execution |
| War Room | `/api/warroom` | Task management, projects, skills, soul files, model config |
| Calendar | `/api/calendar` | Google Calendar via gog CLI |
| Chat | `/api/chat` | Chat interface (rate-limited) |
| Content | `/api/content` | Content Pipeline (Kanban: idea -> draft -> review -> published) |
| Office | `/api/office` | Agent status birds-eye view |
| Activity | `/api/activity` | Activity feed with filtering |

## Data Sources

| Data | Source | Access Method |
|------|--------|---------------|
| Memory files | `~/.openclaw/workspace/memory/*.md` | File read + in-memory cache with file watcher |
| MEMORY.md | `~/.openclaw/workspace/MEMORY.md` | File read |
| Family calendar | Google Calendar (`sollyfamily3@gmail.com`) | `gog` CLI subprocess |
| Agent activity | Postgres (`agent_log`) | Async raw SQL |
| Cron jobs | OpenClaw gateway API (`:18789`) | HTTP |
| Tasks / Projects | `~/.openclaw/workspace/dashboard/data/tasks.json`, `projects.json` | File read/write (thread-locked) |
| Skills | `~/.openclaw/skills/`, `~/.openclaw/workspace/skills/` | Filesystem scan |
| Soul files | `~/.openclaw/workspace/SOUL.md`, `IDENTITY.md`, `USER.md`, `AGENTS.md` | File read/write with 20-entry history |
| OpenClaw config | `~/.openclaw/openclaw.json` | File read/write (model, skill enabled state) |
| Usage sessions | `~/.openclaw/agents/main/sessions/*.jsonl` | Parsed async, 60s TTL cache |
| Content pipeline | `~/.openclaw/workspace/dashboard/data/content.json` | File read/write |
| Activity events | `~/.openclaw/workspace/dashboard/data/activity.json` | File read/write (capped 1000 entries) |

No `memory_entries` table -- memory markdown files are the source of truth. No Redis or message queue.

## Database Schema

Postgres `jeeves` database (shared with legacy Matron system). Key tables used:

- `agent_log` -- agent execution history

Migrations managed via Alembic (`backend/alembic/`). War Room tasks and projects are stored in JSON files, not Postgres.

## Environment Variables

From `.env.example`:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | Postgres connection string | `postgresql+asyncpg://jeeves@localhost:5432/jeeves` |
| `SESSION_SECRET` | Cookie signing key (must change in production) | `change-me` |
| `PORT` | Backend port | `5055` |
| `DEBUG` | Enable debug mode | `true` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `localhost:5173,localhost:5055` |
| `MEMORY_PATH` | Path to memory markdown files | `~/.openclaw/workspace/memory` |
| `OPENCLAW_URL` | OpenClaw gateway for agent triggers | `http://localhost:18789` |
| `CF_ACCESS_TEAM` | Cloudflare Access team (empty = disabled) | empty |

## Coding Conventions

### Backend (Python)

- **Async everywhere** -- all database queries, HTTP calls, and file I/O use async
- **Raw SQL** via SQLAlchemy async sessions -- no ORM models for queries
- **Pydantic v2** for all request/response models (in `models.py` per module)
- **Pydantic Settings** for config (`core/config.py`) -- loads from .env
- **Service layer** pattern: `router.py` (endpoints) -> `service.py` (business logic)
- **ruff** for linting, target Python 3.13, line length 100
- **pytest-asyncio** with `asyncio_mode = "auto"` -- no need for `@pytest.mark.asyncio`
- **Logging** via stdlib logging, not print() or structlog
- **Path handling** via `pathlib.Path.expanduser()` for all user-directory paths

### Frontend (TypeScript/Vue)

- **Composition API** with `<script setup lang="ts">` (no Options API)
- **Pinia stores** for state management (one per module + app-level)
- **PrimeVue** for UI components -- do not add additional UI libraries
- **Apache ECharts** via vue-echarts for charts
- **`@` alias** resolves to `frontend/src/` (configured in vite.config.ts)
- **Generated types** in `src/types/api.ts` -- regenerate after any backend API change
- **Composables** for shared logic: `useApi` (HTTP), `useWebSocket` (WS), `useModule` (module registration)
- **vitest** for unit tests, Playwright for e2e

### Adding a New Module

1. Create `backend/modules/<name>/` with `__init__.py` (MODULE_INFO), `router.py`, `models.py`, `service.py`
2. Create `frontend/src/modules/<name>/` with `routes.ts`, page components, optional store
3. Add `backend/tests/test_<name>.py`
4. Both sides are auto-discovered -- no manual registration needed

## Key Design Decisions

- **Port:** `:5055` dev, `:5050` production (Matron cutover)
- **Agent triggers:** `POST /api/agents/{id}/trigger` sends HTTP to OpenClaw gateway -- Mission Control is the control plane, not the execution engine
- **WebSocket:** Topic-based JSON messages; `useWebSocket` composable handles reconnection with exponential backoff
- **Memory:** Read-only in the UI; edited via filesystem directly
- **CORS:** Dev uses FastAPI middleware; production serves static files via single-origin FastAPI mount
- **Rate limiting:** `slowapi` on sensitive endpoints (e.g., chat: 30/minute)
- **No ORM models:** Raw SQL preferred for query flexibility with existing Postgres schema
- **Session auth over JWT:** Simpler, httpOnly cookies, no token refresh logic

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

## Anti-Patterns

- Do NOT add new UI component libraries -- PrimeVue is the standard
- Do NOT use synchronous database calls -- everything is async
- Do NOT bypass the module contract -- always export MODULE_INFO / routes.ts
- Do NOT store secrets in .env.production -- use .env.production.example as template
- Do NOT modify core/ to support a single module -- modules must be self-contained
- Do NOT use ORM models for queries -- use raw SQL via SQLAlchemy async sessions
- Do NOT skip type generation after API changes -- run `npm run generate-types`
