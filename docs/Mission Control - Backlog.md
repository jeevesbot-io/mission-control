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

- [ ] Phase 1: Scaffolding (FastAPI + Alembic + Vue 3 + Vite + PrimeVue + openapi-typescript pipeline)
- [ ] Phase 2: Shell + theme (layout, dark theme, shared composables)
- [ ] Phase 3: Module — Memory *(killer feature first)*
- [ ] Phase 4: Module — Agents + WebSocket live feed
- [ ] Phase 5: Module — School (side-by-side parity check with Matron)
- [ ] Phase 6: Overview page (widget assembly, stats, health check)
- [ ] Phase 7: Docker + deploy (replace matron-dashboard)
- [ ] Phase 8: Polish + testing

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
- [ ] Migrate `agent_log` history into `agent_runs` via one-time script, then drop `agent_log`
- [ ] Session secret management — move from Docker env var to proper secrets (Docker secrets or mounted file)
