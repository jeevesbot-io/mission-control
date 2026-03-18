"""Tasks module — Postgres-backed task management replacing warroom tasks."""

from .router import router

MODULE_INFO = {
    "id": "tasks",
    "name": "Tasks",
    "icon": "\u2705",
    "router": router,
    "prefix": "/api/tasks",
}
