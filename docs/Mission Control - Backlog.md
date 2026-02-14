---
tags: [jeevesbot, mission-control, backlog]
date created: 2026-02-13
date modified: 2026-02-13
title: Mission Control — Backlog
---

# Mission Control — Backlog

## Pre-Build Decisions (Nick) ✅

- [x] **Port** — new port (`:5055`) during dev, take over `:5050` at cutover
- [x] **External access** — Yes, Tailscale. Session cookies need `Secure` flag + trusted domain.
- [x] **Alerts** — Yes. Flag anomalies (agent hasn't run in expected window, failed runs, etc.)
- [x] **Memory editing** — Read-only in v1. Nick edits via filesystem directly.
- [ ] **First non-agent module** — TBC, parked for now

## Build Phase

- [x] Phase 1: Scaffolding (FastAPI + Alembic + Vue 3 + Vite + PrimeVue + openapi-typescript pipeline) — *done 2026-02-13*
- [x] Phase 2: Shell + theme (layout, dark/light theme, Ground Control design system, shared composables) — *done 2026-02-13*
- [x] Phase 3: Module — Memory (file browser, full-text search, MEMORY.md viewer, TOC nav, RecentMemories widget) — *done 2026-02-13*
- [x] Phase 4: Module — Agents + WebSocket live feed (agent list, log history, cron, triggers, live activity feed, `useWebSocket` composable) — *done 2026-02-13*
- [x] Phase 5: Module — School (Google Calendar via gog CLI, emails, tasks tabbed view, child inference, TodayEvents widget) — *done 2026-02-13*
- [x] Phase 6: Overview page (`/api/overview` endpoint aggregating all data, health checks, upcoming events, agent activity, stat cards, two-column layout) — *done 2026-02-13*
- [x] Phase 7: Docker + deploy (multi-stage Dockerfile, production docker-compose on port 5050, SPA static serving) — *done 2026-02-13*
- [x] Phase 8: Polish + testing (42 backend tests, 41 frontend tests, Playwright e2e suites) — *done 2026-02-13*

## Future Features

- [ ] **PWA support** — installable on phone as a native-feeling app
- [ ] **Notifications** — push alerts for agent failures or urgent items
- [ ] **User preferences** — theme toggle, widget layout customisation
- [ ] **Multi-user** — if family members want their own views (low priority)
- [ ] **Obsidian integration** — embed Mission Control widgets in Obsidian notes
- [ ] **Chat interface** — talk to Jeeves directly from the dashboard (WebSocket to OpenClaw)
- [ ] **Embedding-based search** — upgrade memory search from full-text to semantic (via OpenClaw memory_search API) if full-text isn't sufficient

## Technical Debt / Migration

- [ ] Matron's Flask dashboard decommissioning once School module is live and stable
- [ ] Review `agent_log` table ownership — shared between OpenClaw (writes) and Mission Control (reads)
- [ ] Session secret management — move from Docker env var to proper secrets (Docker secrets or mounted file)
