"""Cron Monitor module — read-only visibility into OpenClaw cron jobs."""

from .router import router

MODULE_INFO = {
    "id": "cron",
    "name": "Cron Monitor",
    "icon": "\u23f0",
    "router": router,
    "prefix": "/api/cron",
}
