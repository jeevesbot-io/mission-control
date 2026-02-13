# Mission Control

Unified dashboard and life operating system. Plugin-based architecture where each life domain (agents, memory, school, health, finance, etc.) is a self-contained module.

Replaces Matron's standalone Flask dashboard with a proper platform — same data, better home.

## Status

**Phase 1 (scaffolding) complete.** Core system, database, and frontend framework are live. Building towards Phase 2 (shell + theme).

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, Python 3.13+, async |
| Frontend | Vue 3, Vite, TypeScript |
| UI | PrimeVue, Apache ECharts |
| State | Pinia |
| Database | Postgres (shared `jeeves` DB) |
| Migrations | Alembic |
| Auth | Signed httpOnly session cookies (itsdangerous) |
| Real-time | WebSocket (`/ws/live`) |
| Type sync | openapi-typescript |
| Package management | uv (backend), npm (frontend) |

## Prerequisites

- Python 3.13+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/)
- Postgres with `jeeves` database
- (Optional) Docker via Colima

## Quick Start

```bash
# Clone and set up environment
cp .env.example .env        # edit DATABASE_URL and SESSION_SECRET

# Backend
cd backend
uv sync                     # install Python deps
uv run alembic upgrade head # run migrations
uv run uvicorn main:app --reload --port 5055

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                 # dev server at http://localhost:5173, proxied to :5055
```

The API is at `http://localhost:5055` with docs at `/docs` (Swagger) and `/redoc`.

## Development

```bash
# Run tests
cd backend && uv run pytest
cd frontend && npm test

# Generate TypeScript types from API (backend must be running)
cd frontend && npm run generate-types
# or: ./scripts/generate-types.sh

# Lint (backend)
cd backend && uv run ruff check .

# Docker (both services)
docker-compose -f docker-compose.dev.yml up
```

## Architecture

Plugin-based monolith with auto-discovery. Adding a module means dropping in a folder — no changes to core code.

```
mission-control/
├── backend/
│   ├── main.py              # App factory, module auto-discovery
│   ├── core/                # Auth, registry, config, DB, WebSocket hub
│   ├── modules/             # One sub-package per domain
│   ├── alembic/             # Migration scripts
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── router/          # Auto-imports module routes
│   │   ├── stores/          # Pinia stores
│   │   ├── modules/         # One sub-folder per domain
│   │   ├── components/      # Shared UI
│   │   └── composables/     # useApi, useWebSocket, useModule
│   └── vite.config.ts
├── docs/                    # Architecture, backlog, module registry
├── scripts/
│   └── generate-types.sh
└── docker-compose.dev.yml
```

### Adding a Module

**Backend** — `backend/modules/<name>/__init__.py`:
```python
MODULE_INFO = {
    "id": "finance",
    "name": "Finance",
    "icon": "\U0001f4b0",
    "router": router,
    "prefix": "/api/finance",
}
```

**Frontend** — `frontend/src/modules/<name>/routes.ts`:
```typescript
export default {
  module: { id: 'finance', name: 'Finance', icon: '\U0001f4b0', navOrder: 5 },
  routes: [{ path: '/finance', component: () => import('./FinancePage.vue') }],
  overviewWidgets: [() => import('./widgets/SpendingSummary.vue')],
}
```

The core discovers and mounts both automatically.

## Build Phases

1. ~~Scaffolding~~ (done)
2. Shell + theme
3. Memory module
4. Agents module + WebSocket
5. School module
6. Overview page
7. Docker + deploy
8. Polish + testing

See `docs/` for full architecture docs, module registry, and backlog.

## Environment Variables

See `.env.example` for all available settings. Key ones:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | Postgres connection string | — |
| `SESSION_SECRET` | Cookie signing key | — |
| `PORT` | Backend port | `5055` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `localhost:5173,localhost:5055` |
| `MEMORY_PATH` | Path to memory markdown files | `~/.openclaw/workspace/memory` |
| `OPENCLAW_URL` | OpenClaw gateway for agent triggers | `http://localhost:18789` |
