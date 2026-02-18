"""War Room module — task management and agent control centre."""

from .router import router

MODULE_INFO = {
    "id": "warroom",
    "name": "War Room",
    "icon": "⚔️",
    "router": router,
    "prefix": "/api/warroom",
}
