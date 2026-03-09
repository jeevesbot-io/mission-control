"""Agent Runs module — centralised logging of all agent activity."""

from .router import router

MODULE_INFO = {
    "id": "runs",
    "name": "Agent Runs",
    "icon": "📊",
    "router": router,
    "prefix": "/api/runs",
}
