"""Agents module — monitor and trigger agent runs."""

from .router import router

MODULE_INFO = {
    "id": "agents",
    "name": "Agents",
    "icon": "\u26a1",  # ⚡
    "router": router,
    "prefix": "/api/agents",
}
