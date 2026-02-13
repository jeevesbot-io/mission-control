"""Memory module — browse and search Jeeves' memory system."""

from .router import router

MODULE_INFO = {
    "id": "memory",
    "name": "Memory",
    "icon": "\U0001f4dc",  # 📜
    "router": router,
    "prefix": "/api/memory",
}
