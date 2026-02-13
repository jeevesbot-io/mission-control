---
tags: [jeevesbot, mission-control, p/clawdbot]
type: moc
date created: 2026-02-13
date modified: 2026-02-13
title: Mission Control — Map of Content
---

# 🧠 Mission Control

A unified dashboard and life operating system built on FastAPI + Vue 3. Plugin-based architecture where each life domain (agents, memory, school, health, finance, etc.) is a self-contained module.

> [!info] Status: **Planning** 📐
> Architecture documented. Awaiting review before build.

---

## Documentation

| Document | Description |
|----------|-------------|
| [[Mission Control - Architecture]] | Full architecture proposal: stack, project structure, API design, wireframes, implementation plan |
| [[Mission Control - Modules]] | Module registry: what exists, what's planned, data sources |
| [[Mission Control - Backlog]] | Issues, ideas, future features |

## Related Agent Docs

| Agent | Docs |
|-------|------|
| 📜 The Archivist | [[Archivist - MOC]] — memory curator, key data source for Memory module |
| 🏥 Matron | [[Matron - MOC]] — school comms, data source for School module |

---

## Quick Reference

- **Stack:** FastAPI + Vue 3 + Vite + PrimeVue + Pinia + Postgres + Alembic
- **Auth:** Session cookies (signed, httpOnly)
- **Deployment:** Docker via Colima
- **Port:** `:5055` dev → `:5050` at Matron cutover
- **Modules (planned):** Overview, Memory, School, Agents, Analytics
- **Build order:** Scaffolding → Shell → Memory → Agents → School → Overview → Deploy → Polish
- **Future modules:** Health, Finance, Reading, Dog Training, ...

---

## Design Principles

1. **Plugin architecture** — adding a domain is dropping in a module folder, not editing core code
2. **API-first** — every feature has a JSON endpoint; UI consumes the API
3. **One source of truth** — modules read from their canonical data sources (Postgres, markdown files, OpenClaw API), never duplicate
4. **Real-time** — WebSocket live feed for agent activity
5. **Mobile-ready** — responsive from day one, potential PWA later
6. **Graceful degradation** — if a data source is down, that module shows "unavailable" while the rest keeps working
