"""Workspace module — heartbeat, usage, model switching, and workspace files."""

from .router import router

MODULE_INFO = {
    "id": "workspace",
    "name": "Workspace",
    "icon": "\U0001f3e0",
    "router": router,
    "prefix": "/api/workspace",
}
