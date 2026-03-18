# Mission Control

Agent orchestration dashboard built on FastAPI + Vue 3. Plugin-based architecture where each module is auto-discovered and self-contained.

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, Python 3.13+, async throughout |
| Frontend | Vue 3, Vite, TypeScript, Composition API |
| UI | PrimeVue, Apache ECharts, Lucide icons |
| State | Pinia |
| Database | Postgres (`jeeves` DB), raw SQL via asyncpg |
| Migrations | Alembic |
| Auth | Signed httpOnly session cookies (itsdangerous), Cloudflare Access in production |
| Real-time | WebSocket (`/ws/live`, topic-based pub/sub) |
| Type sync | openapi-typescript |
| Package management | uv (backend), npm (frontend) |
| Testing | pytest (140 tests), vitest (32 tests), Playwright (e2e) |

## Active Modules

| Module | Prefix | Purpose |
|--------|--------|---------|
| Overview | `/api/overview` | Dashboard home, aggregates widgets from all modules |
| Tasks | `/api/tasks` | Postgres-backed task management (CRUD, queue, claim/release, comments, activity) |
| Agents | `/api/agents` | Agent fleet monitoring, logs, triggers, office view |
| Projects | `/api/projects` | Project management with task counts |
| Skills | `/api/skills` | Skill browser with SHA-256 drift detection |
| Heatmap | `/api/runs` | Activity heatmap from agent run data |
| Activity | `/api/activity` | Cross-module event feed |
| Workspace | `/api/workspace` | Heartbeat, usage monitoring, model switching, workspace files |

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

API docs at `http://localhost:5055/docs` (Swagger) and `/redoc`.

## Development

```bash
# Run tests
cd backend && uv run pytest          # 140 tests
cd frontend && npm test              # 32 tests

# Lint
cd backend && uv run ruff check .

# Generate TypeScript types from API (backend must be running)
cd frontend && npm run generate-types

# Docker
docker-compose -f docker-compose.dev.yml up   # development
docker-compose up                              # production (port 5050)
```

## Architecture

Plugin-based monolith with auto-discovery. Adding a module means dropping in a folder — no changes to core code.

```
mission-control/
├── backend/
│   ├── main.py              # App factory, module auto-discovery, WebSocket, SPA serving
│   ├── core/                # Auth, registry, config, DB, WebSocket hub, rate limiting
│   ├── modules/             # One sub-package per domain
│   │   ├── activity/        # Activity Timeline feed
│   │   ├── agents/          # Agent management + triggers + Office view
│   │   ├── overview/        # Dashboard Overview (widget aggregation)
│   │   ├── projects/        # Project management (Postgres)
│   │   ├── runs/            # Agent run logging + heatmap
│   │   ├── skills/          # Skill browser + drift detection
│   │   ├── tasks/           # Task management (Postgres mc_tasks)
│   │   └── workspace/       # Heartbeat, usage, models, workspace files
│   ├── alembic/             # Database migration scripts
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── router/          # Auto-imports module routes
│   │   ├── stores/          # Pinia stores
│   │   ├── modules/         # One sub-folder per domain
│   │   ├── components/      # Shared UI (layout, data, ui)
│   │   └── composables/     # useApi, useWebSocket, useModule
│   └── e2e/                 # Playwright e2e tests
├── scripts/
│   └── generate-types.sh
├── docker-compose.yml       # Production (port 5050)
└── docker-compose.dev.yml   # Development
```

### Adding a Module

**Backend** — `backend/modules/<name>/__init__.py`:
```python
MODULE_INFO = {
    "id": "module_name",
    "name": "Display Name",
    "icon": "...",
    "router": router,
    "prefix": "/api/module",
}
```

**Frontend** — `frontend/src/modules/<name>/routes.ts`:
```typescript
export default {
  module: { id: 'name', name: 'Display Name', icon: 'icon', navOrder: 5 },
  routes: [{ path: '/name', component: () => import('./Page.vue') }],
}
```

Both sides auto-discover — no manual registration needed.

## Environment Variables

See `.env.example` for all settings. Key ones:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | Postgres connection string | `postgresql+asyncpg://jeeves@localhost:5432/jeeves` |
| `SESSION_SECRET` | Cookie signing key | — |
| `PORT` | Backend port | `5055` |
| `CORS_ORIGINS` | Allowed origins | `localhost:5173,localhost:5055` |
| `OPENCLAW_URL` | OpenClaw gateway for agent triggers | `http://localhost:18789` |
